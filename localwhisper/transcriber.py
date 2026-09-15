"""Módulo de Transcrição Local utilizando o Faster-Whisper.

Este módulo gerencia o carregamento sob demanda do modelo Whisper da OpenAI
otimizado com CTranslate2 (faster-whisper). Ele realiza a transcrição de
áudio local em segundo plano com suporte a VAD (Voice Activity Detection) e
filtros de silêncio para máxima precisão e velocidade.
"""

from __future__ import annotations

import concurrent.futures
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    import numpy as np
    from faster_whisper import WhisperModel

from .config import AppConfig, is_model_downloaded, model_snapshot_path
from .hardware import resolve_hardware

# ---------------------------------------------------------------------------
# Thresholds de qualidade da transcrição (faster-whisper)
# Valores recomendados pela documentação do faster-whisper para uso em produção.
# ---------------------------------------------------------------------------

#: Rejeita segmento se probabilidade de silêncio/não-fala for > este valor.
#: 0.6 = rejeita se 60%+ de chance de não ser fala (conservador).
NO_SPEECH_THRESHOLD: float = 0.6

#: Rejeita segmento se log_prob médio for < este valor.
#: -1.0 = limiar padrão do Whisper original (OpenAI). Mais negativo = mais permissivo.
LOG_PROB_THRESHOLD: float = -1.0

#: Rejeita segmento se o ratio de compressão do texto gerado for > este valor.
#: Valores altos indicam texto repetitivo (loop de alucinação). 2.4 = padrão OpenAI.
COMPRESSION_RATIO_THRESHOLD: float = 2.4

# Tipo para o callback de alteração de status na UI
StatusCallback = Callable[[str], None]


def _vad_runtime_available() -> bool:
    """Retorna se o runtime opcional do filtro VAD está completo.

    O Core distribuído não inclui as bibliotecas nativas do ``onnxruntime``.
    Em builds congelados, o pacote residual pode ser importado, mas sem expor
    ``SessionOptions``. Nessa situação a transcrição comum deve continuar sem
    VAD, em vez de falhar antes de decodificar o áudio.
    """
    try:
        import onnxruntime
    except (ImportError, OSError):
        return False
    return callable(getattr(onnxruntime, "SessionOptions", None))


class LocalTranscriber:
    """Classe responsável pelo ciclo de vida do modelo Whisper e transcrição do áudio."""

    def __init__(self, config: AppConfig, on_status: StatusCallback) -> None:
        """Inicializa o transcritor com as configurações do aplicativo.

        Args:
            config: Objeto com as configurações carregadas do config.json.
            on_status: Função para relatar o progresso do processamento à interface.
        """
        self.config = config
        self.on_status = on_status
        self._model: WhisperModel | None = None
        self._lock = threading.Lock()
        self._decode_lock = threading.Lock()
        self._cancel_event = threading.Event()
        self._current_device: str | None = None
        self._current_compute_type: str | None = None

    def is_loaded(self) -> bool:
        """Retorna True se o modelo já foi carregado na memória."""
        with self._lock:
            return self._model is not None

    def cancel(self) -> None:
        """Sinaliza para cancelar a transcrição atual o mais rápido possível."""
        self._cancel_event.set()

    def load(self) -> None:
        """Carrega o modelo de IA na memória de forma thread-safe se ainda não foi carregado.

        Determina automaticamente se deve rodar em CPU ou CUDA (GPU) e qual
        o tipo de precisão matemática para computação rápida.
        """
        with self._lock:
            if self._model is not None:
                return

            model_name = (
                getattr(self.config, "effective_model", "") or self.config.model
            )
            if not is_model_downloaded(model_name):
                raise RuntimeError(
                    f"O modelo {model_name} ainda não está instalado. "
                    "Abra Configurações > Ditado & IA e confirme o download."
                )

            from faster_whisper import WhisperModel
            model_path = str(model_snapshot_path(model_name))

            selection = resolve_hardware(self.config.device, self.config.compute_type)
            device = selection.device
            compute_type = selection.compute_type
            if self.config.device != "cpu" and device == "cpu":
                self.on_status("CUDA indisponível. Usando CPU...")
                print(f"[Hardware] {selection.detail}. Usando CPU/{compute_type}.")
            else:
                print(f"[Hardware] {selection.detail}. Usando {device}/{compute_type}.")

            # Inicializa o modelo usando o diretório local configurado
            try:
                self._model = WhisperModel(
                    model_path,
                    device=device,
                    compute_type=compute_type,
                )
                self._current_device = device
                self._current_compute_type = compute_type
            except Exception as error:
                # Se falhar ao carregar no CUDA (ex: DLL ausente, driver incompatível, hardware sem NVIDIA)
                if device == "cuda":
                    self.on_status("CUDA indisponível. Recuando para CPU...")
                    device = "cpu"
                    cpu_selection = resolve_hardware("cpu", self.config.compute_type)
                    compute_type = cpu_selection.compute_type
                    self._model = WhisperModel(
                        model_path,
                        device=device,
                        compute_type=compute_type,
                    )
                    self._current_device = device
                    self._current_compute_type = compute_type
                else:
                    raise error

            self.on_status("Pronto — Ctrl+Space para ditar")

    def _build_tone_instruction(self) -> str:
        """Retorna a instrução de tom para o prompt do Whisper."""
        tone = getattr(self.config, "tone_style", "natural")
        custom_tones = getattr(self.config, "custom_tones", {})

        # Tons built-in
        built_in = {
            "natural": "Transcreva em português do Brasil, exatamente como falado. Preserve coloquialismos, gírias e contRAções como 'tô', 'tá', 'né', 'pra', 'pro', 'aí'.",
            "formal": "Transcrição formal e profissional, sem gírias, mantendo a gramática exata e pontuação perfeita.",
            "developer": "Transcrição técnica com termos em inglês e jargões de programação. Exemplo: camelCase, HTML, Python, API."
        }

        # Verifica tons customizados primeiro (têm prioridade sobre built-ins do mesmo nome)
        if tone in custom_tones and custom_tones[tone].strip():
            return custom_tones[tone].strip()

        return built_in.get(tone, built_in["natural"])

    def _literal_mode_enabled(self, translate: bool = False) -> bool:
        """Retorna True quando a saída deve preservar literalmente o ditado."""
        return bool(getattr(self.config, "literal_mode", True)) and not translate

    def _segments_to_text(self, segments, *, translate: bool = False) -> str:
        """Materializa segmentos e restaura pontuação sem trocar palavras."""
        collected = []
        for segment in segments:
            if self._cancel_event.is_set():
                return ""
            collected.append(segment)

        if not bool(getattr(self.config, "punctuation_assist", True)):
            return " ".join(segment.text.strip() for segment in collected).strip()

        from .punctuation import join_whisper_segments

        pause_ms = max(200, int(getattr(self.config, "punctuation_pause_ms", 650)))
        return join_whisper_segments(
            collected,
            pause_threshold_seconds=pause_ms / 1000.0,
            detect_questions=not translate and (self.config.language or "pt") == "pt",
        )

    def transcribe(self, audio_path: Path, translate: bool = False, duration: float | None = None) -> str:
        """Transcreve o arquivo de áudio WAV indicado, com suporte a tradução para o inglês.

        Args:
            audio_path: Caminho local do arquivo .wav gravado.
            translate: Se True, traduz o áudio de qualquer idioma diretamente para o inglês.
            duration: Duração do áudio em segundos (se já conhecida).

        Returns:
            O texto transcrito e limpo.

        Raises:
            TimeoutError: Se a transcrição exceder o tempo limite do watchdog.
        """
        # Garante que o modelo está inicializado antes de transcrever
        self.load()
        assert self._model is not None

        self._cancel_event.clear()
        status_msg = "Traduzindo localmente…" if translate else "Transcrevendo localmente…"
        self.on_status(status_msg)

        # Calcula a duração do áudio em segundos para determinar o timeout do watchdog
        if duration is not None:
            audio_duration_s = duration
        else:
            try:
                import wave
                with wave.open(str(audio_path), "rb") as wave_file:
                    frames = wave_file.getnframes()
                    rate = wave_file.getframerate()
                    audio_duration_s = frames / float(rate)
            except Exception:
                audio_duration_s = 5.0  # Assume médio se não conseguir ler

        # Watchdog: executa a decodificação em executor com timeout dinâmico
        # Fórmula: max(180.0, audio_duration_s * 5)
        # Isso garante tempo suficiente para qualquer gravação longa sem travamentos.
        WATCHDOG_TIMEOUT = max(180.0, audio_duration_s * 5.0)

        task = "translate" if translate else "transcribe"
        literal_mode = self._literal_mode_enabled(translate)

        # Mantém as opções de decodificação fora da função executada pelo watchdog
        # para que o fallback CUDA -> CPU reutilize exatamente os mesmos parâmetros.
        if audio_duration_s < 2.0:
            beam_size = 1
        elif audio_duration_s < 5.0:
            beam_size = 3
        else:
            beam_size = 5

        prompt = None
        if not translate and not literal_mode:
            base_prompt = self._build_tone_instruction()

            if getattr(self.config, "continuous_learning", False):
                try:
                    from .memory import get_active_vocabulary

                    vocab = get_active_vocabulary()
                    if vocab:
                        base_prompt += f" Vocabulário frequente: {vocab}."
                except Exception as error:
                    import logging

                    logging.getLogger(__name__).warning(
                        f"[Transcriber] Falha ao carregar vocabulário ativo: {error}",
                        exc_info=True,
                    )

            try:
                from .vocab_cache import personal_vocab

                vocab_hint = personal_vocab.get_whisper_vocab_hint(max_words=15)
                if vocab_hint:
                    base_prompt += f" Nomes e termos: {vocab_hint}."
            except Exception as error:
                import logging

                logging.getLogger(__name__).warning(
                    f"[Transcriber] Falha ao carregar vocabulário pessoal: {error}",
                    exc_info=True,
                )

            if self.config.initial_prompt:
                base_prompt += f" {self.config.initial_prompt}"
            prompt = base_prompt

        vad_filter = _vad_runtime_available()
        decode_options = {
            "language": self.config.language or None,
            "task": task,
            "beam_size": beam_size,
            "vad_filter": vad_filter,
            "condition_on_previous_text": not literal_mode,
            "initial_prompt": prompt,
            "no_speech_threshold": NO_SPEECH_THRESHOLD,
            "log_prob_threshold": LOG_PROB_THRESHOLD,
            "compression_ratio_threshold": COMPRESSION_RATIO_THRESHOLD,
        }
        if vad_filter:
            decode_options["vad_parameters"] = {"min_silence_duration_ms": 400}

        def _run_decode() -> str:
            """Executa a decodificação completa e coleta os segmentos."""
            with self._decode_lock:
                segments, transcription_info = self._model.transcribe(  # type: ignore[union-attr]
                    str(audio_path),
                    **decode_options,
                )

                # Força a avaliação das sentenças. Como segments é um gerador preguiçoso (lazy),
                # erros de carregamento tardio de DLLs CUDA só ocorrerão ao iterar pelos resultados!
                raw_text = self._segments_to_text(segments, translate=translate)
            return raw_text

        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        try:
            future = executor.submit(_run_decode)
            try:
                return future.result(timeout=WATCHDOG_TIMEOUT)
            except concurrent.futures.TimeoutError:
                self._cancel_event.set()  # Sinaliza para a thread parar
                executor.shutdown(wait=False)  # Não bloqueia — abandona a thread
                raise TimeoutError(
                    f"Transcrição excedeu {WATCHDOG_TIMEOUT:.0f}s. "
                    "Verifique o modelo ou áudio."
                )
        except TimeoutError:
            raise
        except Exception as error:
            executor.shutdown(wait=False)
            # Se ocorrer um erro durante a decodificação usando GPU CUDA, recua para CPU
            with self._lock:
                is_cuda = (self._current_device == "cuda")

            if is_cuda:
                import logging
                logging.getLogger(__name__).warning(f"[Transcriber] Falha na decodificação via GPU CUDA: {error}. Recuando para CPU...", exc_info=True)
                self.on_status("Erro na GPU. Recuando para CPU...")
                with self._lock:
                    self._model = None  # Descarrega o modelo defeituoso da GPU

                # Recarrega na CPU de forma forçada
                with self._lock:
                    from faster_whisper import WhisperModel
                    device = "cpu"
                    cpu_selection = resolve_hardware("cpu", self.config.compute_type)
                    compute_type = cpu_selection.compute_type
                    self._model = WhisperModel(
                        str(
                            model_snapshot_path(
                                getattr(self.config, "effective_model", self.config.model) or self.config.model
                            )
                        ),
                        device=device,
                        compute_type=compute_type,
                    )
                    self._current_device = device
                    self._current_compute_type = compute_type

                # Tenta novamente a transcrição usando o novo modelo em CPU
                # (sem watchdog extra — já estamos em fallback)
                with self._decode_lock:
                    segments, transcription_info = self._model.transcribe(
                        str(audio_path),
                        **decode_options,
                    )
                    raw_text = self._segments_to_text(segments, translate=translate)
                return raw_text
            else:
                raise error
        finally:
            try:
                executor.shutdown(wait=False)
            except Exception:
                pass

    def transcribe_numpy(
        self,
        audio_float32: np.ndarray,
        context_prompt: str = "",
        translate: bool = False,
    ) -> str:
        """Transcreve áudio a partir de um array numpy float32 (modo streaming).

        Usado pelo StreamTranscriber para evitar salvar/carregar arquivos WAV
        intermediários, reduzindo a latência. O faster-whisper aceita arrays
        numpy float32 normalizados em [-1, 1] diretamente.

        Args:
            audio_float32: Array float32 mono 16kHz em [-1.0, 1.0].
            context_prompt: Texto do chunk anterior (mantém continuidade de contexto).
            translate: Se True, traduz o áudio para inglês.

        Returns:
            O texto transcrito e limpo.
        """
        # Garante que o modelo está inicializado
        self.load()
        assert self._model is not None

        self._cancel_event.clear()
        task = "translate" if translate else "transcribe"
        literal_mode = self._literal_mode_enabled(translate)

        # Constrói o prompt combinando contexto anterior + tom + vocab
        prompt: str | None = None
        if not translate and not literal_mode:
            tone = getattr(self.config, 'tone_style', 'natural')
            tone_hints = {
                "natural": "Português do Brasil coloquial, exatamente como falado.",
                "formal": "Português formal e profissional.",
                "developer": "Técnico com jargões de programação em inglês.",
            }
            base = tone_hints.get(tone, tone_hints["natural"])

            if self.config.initial_prompt:
                base = self.config.initial_prompt + " " + base

            if getattr(self.config, 'continuous_learning', False):
                try:
                    from .memory import get_active_vocabulary
                    vocab = get_active_vocabulary()
                    if vocab:
                        base += f" Vocábulário: {vocab}."
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).warning(f"[Transcriber] Falha ao carregar vocabulário ativo (numpy): {e}", exc_info=True)

            try:
                from .vocab_cache import personal_vocab
                vocab_hint = personal_vocab.get_whisper_vocab_hint(max_words=15)
                if vocab_hint:
                    base += f" Termos: {vocab_hint}."
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"[Transcriber] Falha ao carregar vocabulário pessoal (numpy): {e}", exc_info=True)

            # Prefixa com as últimas palavras do chunk anterior para continuidade
            prompt = (context_prompt + " " + base).strip() if context_prompt else base

        # Beam size adaptativo para streaming: chunks curtos usam greedy
        _stream_duration_s = len(audio_float32) / 16000  # SAMPLE_RATE = 16000
        if _stream_duration_s < 2.0:
            _stream_beam = 1
        elif _stream_duration_s < 5.0:
            _stream_beam = 3
        else:
            _stream_beam = 5

        with self._decode_lock:
            segments, transcription_info = self._model.transcribe(  # type: ignore[union-attr]
                audio_float32,
                language=self.config.language or None,
                task=task,
                beam_size=_stream_beam,
                vad_filter=False,  # VAD já foi feito pelo StreamTranscriber
                condition_on_previous_text=not literal_mode,
                initial_prompt=prompt,
                # --- Filtros de confiança ---
                no_speech_threshold=NO_SPEECH_THRESHOLD,
                log_prob_threshold=LOG_PROB_THRESHOLD,
                compression_ratio_threshold=COMPRESSION_RATIO_THRESHOLD,
            )

            return self._segments_to_text(segments, translate=translate)

    def reload_config(self, config: AppConfig) -> None:
        """Atualiza a referência de configuração e descarrega o modelo se parâmetros críticos mudaram."""
        with self._lock:
            # Se mudou modelo, device ou compute_type, limpa o modelo carregado para recarregar sob demanda
            old_model = getattr(self.config, "effective_model", self.config.model) or self.config.model
            new_model = getattr(config, "effective_model", config.model) or config.model
            if (old_model != new_model or
                self.config.device != config.device or
                self.config.compute_type != config.compute_type):
                self._model = None
                self._current_device = None
                self._current_compute_type = None
            self.config = config
