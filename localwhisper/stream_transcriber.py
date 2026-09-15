"""Transcritor de Streaming Inteligente com VAD Word-Boundary-Aware.

Implementa transcrição contínua e em paralelo com as seguintes características:

    Chunking inteligente:
        - Detecta limites naturais de fala via VAD (Voice Activity Detection)
        - Nunca corta no meio de uma palavra ou sílaba
        - Chunks de MIN_CHUNK_SECONDS a MAX_CHUNK_SECONDS
        - Silêncio de MIN_SILENCE_MS após fala suficiente = ponto de corte natural

    VAD (Voice Activity Detection):
        - Silero VAD (principal): modelo neural leve, altamente preciso mesmo com
          ruído de fundo, voz baixa ou microfone barato.
        - Energy VAD (fallback): baseado em RMS, sem dependências extras.
          Ativado automaticamente enquanto o componente Silero não está instalado.

    Pipeline de qualidade:
        - Áudio aprimorado via AudioEnhancer antes de enviar ao Whisper
        - Texto limpo via SpeechCleaner (gageiras, fillers, alucinações)
        - Correções de vocabulário pessoal via PersonalVocabCache
        - Contexto mantido entre chunks via initial_prompt acumulado

    Paralelismo:
        - Áudio é capturado continuamente enquanto o chunk anterior é transcrito
        - ThreadPoolExecutor com 2 workers: 1 transcrevendo, 1 de reserva
        - Zero bloqueio do loop de captura de áudio

Uso típico (via app.py):
    session = StreamTranscriber(config, on_chunk_text=..., on_status=..., on_error=...)
    session.start(transcriber_instance, device_index=None)
    # ... usuário fala ...
    full_text = session.stop()  # Para e retorna o texto acumulado
"""

from __future__ import annotations

import concurrent.futures
import logging
import queue
import threading
from typing import TYPE_CHECKING, Callable, Optional

import numpy as np

if TYPE_CHECKING:
    import sounddevice as sd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constantes de configuração do streaming
# ---------------------------------------------------------------------------

SAMPLE_RATE: int = 16_000

#: Mínimo de segundos de fala antes de considerar cortar o chunk
MIN_CHUNK_SECONDS: float = 3.5

#: Máximo de segundos de qualquer chunk (força corte mesmo sem pausa)
MAX_CHUNK_SECONDS: float = 8.0

#: Silêncio mínimo em ms para considerar fim de palavra/frase
MIN_SILENCE_MS: int = 350

#: Frame de VAD em amostras. Silero exige exatamente 512 @ 16kHz (32ms)
VAD_FRAME_SAMPLES: int = 512

#: Amostras mínimas de áudio para tentar transcrição (0.4s)
MIN_TRANSCRIPTION_SAMPLES: int = int(SAMPLE_RATE * 0.4)

#: Número máximo de amostras a manter no buffer global (~10 min)
MAX_BUFFER_SAMPLES: int = SAMPLE_RATE * 600

#: Número de amostras de overlap entre chunks para preservar contexto de borda
OVERLAP_SAMPLES: int = int(SAMPLE_RATE * 0.3)


# ===========================================================================
# VAD Implementations
# ===========================================================================

class _SileroVAD:
    """Silero VAD v5 via ONNX Runtime, sem carregar o PyTorch.

    O modelo neural é o mesmo da distribuição oficial do Silero. Apenas o
    adaptador tensorial foi trocado por NumPy para evitar centenas de MB de
    dependências que não alteravam a qualidade da detecção.
    """

    def __init__(self, min_silence_ms: int = MIN_SILENCE_MS) -> None:
        from .components import component_dir, component_installed

        if not component_installed("silero_vad"):
            raise RuntimeError("componente Silero VAD ainda não instalado")
        import onnxruntime as ort

        options = ort.SessionOptions()
        options.inter_op_num_threads = 1
        options.intra_op_num_threads = 1
        self._session = ort.InferenceSession(
            str(component_dir("silero_vad") / "silero_vad.onnx"),
            providers=["CPUExecutionProvider"],
            sess_options=options,
        )
        self._threshold = 0.5
        self._min_silence_samples = SAMPLE_RATE * min_silence_ms / 1000
        self._speech_pad_samples = SAMPLE_RATE * 80 / 1000
        self.reset()

    def process_frame(self, frame_int16: np.ndarray) -> dict | None:
        """Processa um frame de 512 amostras.

        Args:
            frame_int16: Array int16 com exatamente 512 amostras.

        Returns:
            {'start': seconds} quando speech começa,
            {'end': seconds} quando speech termina,
            None se sem mudança de estado.
        """
        if len(frame_int16) != VAD_FRAME_SAMPLES:
            raise ValueError(f"Silero VAD requer {VAD_FRAME_SAMPLES} amostras por frame")
        frame = (frame_int16.astype(np.float32) / 32768.0).reshape(1, -1)
        combined = np.concatenate((self._context, frame), axis=1)
        outputs = self._session.run(
            None,
            {"input": combined, "state": self._state, "sr": np.array(SAMPLE_RATE, dtype=np.int64)},
        )
        probability = float(np.asarray(outputs[0]).reshape(-1)[0])
        self._state = np.asarray(outputs[1], dtype=np.float32)
        self._context = combined[:, -64:]
        self._sample_cursor += len(frame_int16)

        if probability >= self._threshold and self._temporary_end:
            self._temporary_end = 0
        if probability >= self._threshold and not self._triggered:
            self._triggered = True
            start = max(0, self._sample_cursor - self._speech_pad_samples - len(frame_int16))
            return {"start": round(start / SAMPLE_RATE, 1)}
        if probability < self._threshold - 0.15 and self._triggered:
            if not self._temporary_end:
                self._temporary_end = self._sample_cursor
            if self._sample_cursor - self._temporary_end >= self._min_silence_samples:
                end = self._temporary_end + self._speech_pad_samples - len(frame_int16)
                self._temporary_end = 0
                self._triggered = False
                return {"end": round(end / SAMPLE_RATE, 1)}
        return None

    def reset(self) -> None:
        """Reinicia o estado interno do VAD (para nova sessão)."""
        self._state = np.zeros((2, 1, 128), dtype=np.float32)
        self._context = np.zeros((1, 64), dtype=np.float32)
        self._triggered = False
        self._temporary_end = 0
        self._sample_cursor = 0


class _EnergyVAD:
    """VAD baseado em energia (RMS) — fallback sem dependências extras.

    Menos preciso que o Silero em ambientes ruidosos, mas funciona bem
    em ambientes silenciosos e não requer torch.

    Estratégia: janela deslizante de frames de energia para suavizar
    decisões e evitar falsos positivos em consoantes explosivas (p, t, k).
    """

    def __init__(
        self,
        min_silence_ms: int = MIN_SILENCE_MS,
        speech_threshold: float = 0.012,  # RMS ~-38dBFS
        speech_window: int = 5,           # Frames para suavizar decisão
    ) -> None:
        self._min_silence_samples = int(min_silence_ms * SAMPLE_RATE / 1000)
        self._threshold = speech_threshold
        self._window = speech_window

        self._is_speaking: bool = False
        self._silence_samples: int = 0
        self._sample_cursor: int = 0
        self._energy_history: list[float] = []

    def process_frame(self, frame_int16: np.ndarray) -> dict | None:
        """Processa um frame de áudio e emite eventos de speech start/end."""
        n = len(frame_int16)
        self._sample_cursor += n

        # Calcula RMS normalizado do frame
        audio_f = frame_int16.astype(np.float32) / 32768.0
        rms = float(np.sqrt(np.mean(audio_f ** 2)))

        # Janela deslizante de energia para suavização
        self._energy_history.append(rms)
        if len(self._energy_history) > self._window:
            self._energy_history.pop(0)
        smoothed_rms = sum(self._energy_history) / len(self._energy_history)

        is_speech = smoothed_rms > self._threshold
        seconds = self._sample_cursor / SAMPLE_RATE

        if is_speech:
            self._silence_samples = 0
            if not self._is_speaking:
                self._is_speaking = True
                return {"start": seconds}
        else:
            if self._is_speaking:
                self._silence_samples += n
                if self._silence_samples >= self._min_silence_samples:
                    self._is_speaking = False
                    return {"end": seconds}

        return None

    def reset(self) -> None:
        """Reinicia o estado do VAD."""
        self._is_speaking = False
        self._silence_samples = 0
        self._sample_cursor = 0
        self._energy_history = []


def _create_best_vad(min_silence_ms: int = MIN_SILENCE_MS) -> _SileroVAD | _EnergyVAD:
    """Instancia o melhor VAD disponível.

    Tenta Silero VAD primeiro (melhor qualidade). Se o componente opcional
    ainda não estiver instalado, usa o EnergyVAD como fallback transparente.

    Returns:
        Instância de VAD pronta para uso.
    """
    try:
        vad = _SileroVAD(min_silence_ms=min_silence_ms)
        logger.info("[StreamTranscriber] Silero VAD carregado (alta qualidade).")
        return vad
    except Exception as e:
        logger.warning(
            f"[StreamTranscriber] Silero VAD indisponível ({e}). "
            "Usando Energy VAD como fallback."
        )
        return _EnergyVAD(min_silence_ms=min_silence_ms)


def is_silero_available() -> bool:
    """Verifica se o modelo Silero opcional e o runtime ONNX estão prontos."""
    try:
        import onnxruntime

        from .components import component_installed

        return callable(getattr(onnxruntime, "SessionOptions", None)) and component_installed("silero_vad")
    except (ImportError, OSError, ValueError):
        return False


# ===========================================================================
# StreamTranscriber — Motor Principal
# ===========================================================================

class StreamTranscriber:
    """Motor de transcrição contínua com VAD word-boundary-aware.

    Fluxo de dados:
        Microfone → callback de áudio → buffer circular
                                             ↓
                              VAD processa frames de 32ms
                                             ↓
                  (speech_end detectado E chunk >= MIN_CHUNK_SECONDS)
                                             ↓
                     ThreadPool → enhance_audio → Whisper → clean → deliver

    Uso:
        session = StreamTranscriber(config, on_chunk_text=cb, on_status=status_cb)
        session.start(transcriber, device_index=None)
        # ... usuário fala ...
        full_text = session.stop()

    Callbacks:
        on_chunk_text(text: str):
            Chamado a cada chunk transcrito com sucesso. Texto já limpo.
        on_status(msg: str):
            Chamado com mensagens de status para o HUD (thread-safe via after()).
        on_error(msg: str):
            Chamado se um chunk falhar ao transcrever (não fatal).
    """

    def __init__(
        self,
        config,
        on_chunk_text: Callable[[str], None],
        on_status: Callable[[str], None],
        on_error: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.config = config
        self.on_chunk_text = on_chunk_text
        self.on_status = on_status
        self.on_error = on_error or (lambda e: None)

        # ---- Buffer de áudio ------------------------------------------------
        # Lista de arrays int16 capturados — concatenados sob demanda
        self._audio_chunks: list[np.ndarray] = []
        self._buffer_lock = threading.Lock()
        self._total_samples: int = 0

        # ---- Estado do chunking --------------------------------------------
        # Índice global de amostra onde o chunk atual começa
        self._chunk_start_sample: int = 0

        # ---- VAD -----------------------------------------------------------
        self._vad: _SileroVAD | _EnergyVAD | None = None
        # Acumulador de amostras para completar frames de 512
        self._vad_acc: np.ndarray = np.array([], dtype=np.int16)

        # ---- Estado da máquina de fala -------------------------------------
        self._is_speaking: bool = False
        self._speech_start_sample: int | None = None  # Quando speech começou (amostra global)
        self._chunk_speech_samples: int = 0           # Amostras de fala no chunk atual

        # ---- Parâmetros dinâmicos de chunking --------------------------------
        self._min_chunk_seconds: float = MIN_CHUNK_SECONDS
        self._max_chunk_seconds: float = MAX_CHUNK_SECONDS

        # ---- Execução paralela ---------------------------------------------
        self._executor: concurrent.futures.ThreadPoolExecutor | None = None
        self._pending_futures: list[concurrent.futures.Future] = []

        # ---- Estado da fila ordenada (Fase 3) ------------------------------
        self._output_lock = threading.Lock()
        self._output_buffer: dict[int, str] = {}
        self._next_output_id: int = 0

        # ---- Contexto entre chunks -----------------------------------------
        self._context_prompt: str = ""   # Últimas palavras do chunk anterior
        self._accumulated_text: list[str] = []

        # ---- Stream de áudio -----------------------------------------------
        self._stream: "sd.InputStream" | None = None
        self._running: bool = False
        self._lifecycle_lock = threading.RLock()
        self._cancel_requested = threading.Event()
        self._start_cancelled = threading.Event()
        self._last_amplitude: float = 0.0
        self._amplitude_lock = threading.Lock()

        # ---- Referência ao transcriber -------------------------------------
        self._transcriber = None

        # ---- Fila de chunks para transcrição --------------------------------
        # Garante que chunks são processados em ordem mesmo com threads múltiplas
        self._result_queue: queue.Queue = queue.Queue()
        self._chunk_counter: int = 0  # Para controle de ordem

        # ---- Fila de áudio e thread de processamento VAD --------------------
        self._audio_queue: queue.Queue[np.ndarray | None] = queue.Queue()
        self._processing_thread: threading.Thread | None = None

    # =========================================================================
    # Controle do ciclo de vida
    # =========================================================================

    def start(self, transcriber, device_index: int | None = None) -> None:
        """Inicia a captura de áudio e o pipeline de transcrição.

        Args:
            transcriber: Instância de LocalTranscriber com modelo já carregado.
            device_index: Índice do dispositivo de áudio (None = padrão do sistema).
        """
        with self._lifecycle_lock:
            if self._start_cancelled.is_set():
                return
            self._transcriber = transcriber
            self._running = True

        # Reinicia estado
        self._audio_chunks = []
        self._total_samples = 0
        self._chunk_start_sample = 0
        self._vad_acc = np.array([], dtype=np.int16)
        self._is_speaking = False
        self._speech_start_sample = None
        self._chunk_speech_samples = 0
        self._context_prompt = ""
        self._accumulated_text = []
        self._pending_futures = []
        self._chunk_counter = 0
        self._output_buffer = {}
        self._next_output_id = 0

        # Limpa a fila caso tenha sobrado algo de sessões anteriores
        with self._audio_queue.mutex:
            self._audio_queue.queue.clear()
            self._audio_queue.all_tasks_done.notify_all()
            self._audio_queue.unfinished_tasks = 0

        # Lê chunk_seconds da config (com clamp de segurança: 2.0 a 15.0s)
        chunk_target = float(getattr(self.config, "stream_chunk_seconds", 5.0))
        chunk_target = max(2.0, min(15.0, chunk_target))

        # Define min/max dinamicamente a partir do valor configurado
        self._min_chunk_seconds = chunk_target * 0.7   # ex: 5.0 -> min=3.5s
        self._max_chunk_seconds = chunk_target * 1.6   # ex: 5.0 -> max=8.0s

        # Carrega o VAD
        min_silence = int(getattr(self.config, "stream_min_silence_ms", MIN_SILENCE_MS))
        self._vad = _create_best_vad(min_silence_ms=min_silence)

        # Inicia a thread secundária para consumir da fila e processar áudio/VAD
        self._processing_thread = threading.Thread(
            target=self._process_audio_loop,
            name="stream_process_audio",
            daemon=True
        )
        self._processing_thread.start()

        if self._start_cancelled.is_set():
            return

        # Pool de threads: 2 workers para processamento paralelo real ordenado
        self._executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=2,
            thread_name_prefix="stream_transcribe",
        )

        if self._start_cancelled.is_set():
            self._executor.shutdown(wait=False, cancel_futures=True)
            self._executor = None
            return

        # Inicia o stream de áudio
        import sounddevice as sd
        with self._lifecycle_lock:
            if self._start_cancelled.is_set():
                return
            stream = sd.InputStream(
                device=device_index,
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype="int16",
                blocksize=512,  # Alinhado com o frame do VAD para menor latência
                callback=self._audio_callback,
            )
            self._stream = stream
            stream.start()
            if self._start_cancelled.is_set():
                try:
                    stream.abort()
                    stream.close()
                except Exception:
                    pass
                self._stream = None
                self._running = False
                return
        self.on_status("🔴 Streaming ativo…")

    def stop(self) -> str:
        """Para o streaming e retorna o texto acumulado completo.

        Aguarda a conclusão de todos os chunks em processamento antes de retornar.

        Returns:
            Todo o texto transcrito na sessão, concatenado e limpo.
        """
        # Também impede que uma thread de start ainda em preparação abra o
        # microfone depois deste stop.
        self._start_cancelled.set()
        self._running = False

        # 1. Para o stream de áudio PRIMEIRO para garantir que nenhum callback
        #    adicione mais dados à fila após a sentinela de parada.
        if self._stream:
            try:
                self._stream.stop()  # Bloqueia até o callback atual terminar
                self._stream.close()
            except Exception:
                pass
            self._stream = None

        # 2. Agora que o stream está fechado, nenhum callback pode mais enfileirar.
        #    É seguro enviar a sentinela de parada.
        self._audio_queue.put(None)

        # Aguarda a thread de processamento terminar de esvaziar os frames pendentes
        if self._processing_thread:
            try:
                self._processing_thread.join(timeout=5.0)
            except Exception:
                pass
            self._processing_thread = None

        # Transcreve qualquer áudio restante no buffer (chunk final)
        remaining = self._total_samples - self._chunk_start_sample
        if remaining >= MIN_TRANSCRIPTION_SAMPLES:
            self._trigger_transcription(is_final=True)

        # Aguarda todos os futures pendentes
        for f in self._pending_futures:
            try:
                f.result(timeout=30.0)
            except Exception as e:
                logger.warning(f"[StreamTranscriber] Chunk falhou: {e}")

        # Encerra o executor
        if self._executor:
            self._executor.shutdown(wait=False)
            self._executor = None

        return " ".join(self._accumulated_text).strip()

    def cancel(self) -> None:
        """Cancela o streaming imediatamente sem processar áudio pendente."""
        self._cancel_requested.set()
        self._start_cancelled.set()
        self._running = False

        # Envia sinalizador de parada para a thread de processamento
        self._audio_queue.put(None)

        if self._stream:
            try:
                self._stream.abort()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

        if self._processing_thread:
            try:
                self._processing_thread.join(timeout=2.0)
            except Exception:
                pass
            self._processing_thread = None

        if self._executor:
            self._executor.shutdown(wait=False, cancel_futures=True)
            self._executor = None

    def get_last_amplitude(self) -> float:
        """Retorna o último nível de amplitude para animar o HUD."""
        with self._amplitude_lock:
            return self._last_amplitude

    @property
    def accumulated_text_preview(self) -> str:
        """Retorna o texto acumulado até agora (para exibição no HUD)."""
        return " ".join(self._accumulated_text)

    # =========================================================================
    # Callback de áudio (chamado pelo sounddevice em thread separada)
    # =========================================================================

    def _process_audio_loop(self) -> None:
        """Loop executado em thread secundária para consumir o áudio capturado e rodar o VAD.

        Isso desacopla a thread de captura do sounddevice do processamento neural/GIL.
        """
        while True:
            try:
                flat = self._audio_queue.get()
                if flat is None:
                    # Sentinela de parada
                    self._audio_queue.task_done()
                    break

                if self._cancel_requested.is_set():
                    self._audio_queue.task_done()
                    continue

                n = len(flat)

                # Adiciona ao buffer global de forma thread-safe
                with self._buffer_lock:
                    self._audio_chunks.append(flat)
                    self._total_samples += n
                    # Evita crescimento ilimitado do buffer (máx ~60s)
                    if self._total_samples > MAX_BUFFER_SAMPLES:
                        self._prune_buffer_locked()

                # Alimenta o VAD frame a frame (512 amostras por vez)
                self._vad_acc = np.concatenate([self._vad_acc, flat])
                while len(self._vad_acc) >= VAD_FRAME_SAMPLES:
                    frame = self._vad_acc[:VAD_FRAME_SAMPLES]
                    self._vad_acc = self._vad_acc[VAD_FRAME_SAMPLES:]
                    self._process_vad_frame(frame)

                self._audio_queue.task_done()
            except Exception as e:
                logger.error(f"[StreamTranscriber] Erro no processamento de áudio secundário: {e}", exc_info=True)
                import time
                time.sleep(0.1)

    # =========================================================================
    # Callback de áudio (chamado pelo sounddevice em thread separada)
    # =========================================================================

    def _audio_callback(
        self,
        indata: np.ndarray,
        frames: int,
        time_info: object,
        status: "sd.CallbackFlags",
    ) -> None:
        """Callback do sounddevice — processa cada bloco de áudio capturado.

        Esta função roda em uma thread de alta prioridade do sounddevice.
        Deve ser rápida: apenas copia dados e deposita na fila.
        """
        if not self._running or self._cancel_requested.is_set():
            return
        if status.input_overflow:
            logger.debug("[StreamTranscriber] Input overflow — chunk perdido.")
            return

        flat = indata.flatten().copy()
        n = len(flat)

        # Calcula amplitude para o HUD
        if n > 0:
            rms = float(np.sqrt(np.mean(flat.astype(np.float32) ** 2)))
            with self._amplitude_lock:
                self._last_amplitude = rms / 32768.0

        # Envia para processamento assíncrono fora da thread do driver de áudio
        self._audio_queue.put(flat)

    # =========================================================================
    # Máquina de estados do VAD
    # =========================================================================

    def _process_vad_frame(self, frame: np.ndarray) -> None:
        """Processa um frame de VAD e decide se deve cortar o chunk.

        Máquina de estados:
            IDLE → SPEAKING: VAD detectou início de fala
            SPEAKING → (permanecer): Fala continua
            SPEAKING → TRIGGER: (pausa detectada E fala suficiente) OU (max alcançado)
            TRIGGER → IDLE: Chunk enviado para transcrição, novo chunk começa
        """
        if self._vad is None:
            return

        event = self._vad.process_frame(frame)
        current_sample = self._total_samples  # Aproximação thread-safe

        if event is not None:
            if "start" in event:
                # Início de fala detectado
                if not self._is_speaking:
                    self._is_speaking = True
                    self._speech_start_sample = current_sample

            elif "end" in event:
                # Fim de fala detectado (pausa suficiente)
                if self._is_speaking:
                    self._is_speaking = False

                    # Calcula duração da fala no chunk atual
                    chunk_speech_duration = (
                        current_sample - self._chunk_start_sample
                    ) / SAMPLE_RATE

                    if chunk_speech_duration >= self._min_chunk_seconds:
                        # Fala suficiente + pausa natural = ponto de corte ideal
                        self._trigger_transcription()

        # Verifica força de corte por tamanho máximo (usuário falou sem parar)
        chunk_total_duration = (
            current_sample - self._chunk_start_sample
        ) / SAMPLE_RATE
        if chunk_total_duration >= self._max_chunk_seconds:
            self._trigger_transcription(force=True)

    # =========================================================================
    # Extração e disparo de transcrição
    # =========================================================================

    def _get_chunk_audio(self) -> np.ndarray | None:
        """Extrai o áudio do chunk atual do buffer de forma thread-safe.

        Avança o ponteiro chunk_start para o fim do chunk atual.
        Aplica OVERLAP_SAMPLES de sobreposição para preservar contexto de borda.

        Returns:
            Array int16 do chunk, ou None se não há áudio suficiente.
        """
        with self._buffer_lock:
            if not self._audio_chunks:
                return None

            # Concatena todo o buffer capturado até agora
            full_audio = np.concatenate(self._audio_chunks)
            chunk_start = self._chunk_start_sample
            chunk_end = min(self._total_samples, len(full_audio))

            chunk_length = chunk_end - chunk_start
            if chunk_length < MIN_TRANSCRIPTION_SAMPLES:
                return None

            chunk = full_audio[chunk_start:chunk_end].copy()

            # O novo início do buffer será a margem de overlap antes do final do chunk atual
            new_start = max(chunk_start, chunk_end - OVERLAP_SAMPLES)

            # Reconstrói self._audio_chunks contendo apenas a sobra (overlap + amostras pós chunk_end)
            remaining_audio = full_audio[new_start:]
            if len(remaining_audio) > 0:
                self._audio_chunks = [remaining_audio]
                self._total_samples = len(remaining_audio)
            else:
                self._audio_chunks = []
                self._total_samples = 0

            self._chunk_start_sample = 0

        return chunk

    def _trigger_transcription(
        self,
        force: bool = False,
        is_final: bool = False,
    ) -> None:
        """Extrai o chunk atual e envia para transcrição em background.

        Args:
            force: Se True, corta mesmo sem pausa natural (max_chunk atingido).
            is_final: Se True, é o último chunk da sessão.
        """
        if self._executor is None or not self._running and not is_final:
            return

        chunk = self._get_chunk_audio()
        if chunk is None or len(chunk) < MIN_TRANSCRIPTION_SAMPLES:
            return

        # Captura o contexto atual para passar ao worker (thread-safe por cópia)
        context = self._context_prompt
        chunk_id = self._chunk_counter
        self._chunk_counter += 1

        # Reinicia VAD para o novo chunk
        if self._vad is not None:
            self._vad.reset()
        self._is_speaking = False
        self._speech_start_sample = None

        # Log de diagnóstico
        duration_s = len(chunk) / SAMPLE_RATE
        mode = "FINAL" if is_final else ("FORCE" if force else "VAD")
        logger.debug(
            f"[StreamTranscriber] Chunk #{chunk_id} disparado "
            f"({duration_s:.1f}s, modo={mode})"
        )

        # Submete ao pool de threads
        if self._executor:
            future = self._executor.submit(
                self._do_transcribe,
                chunk,
                context,
                chunk_id,
            )
            self._pending_futures.append(future)

            # Limpa futures já concluídas para não acumular na lista
            self._pending_futures = [
                f for f in self._pending_futures if not f.done()
            ]

    def _prune_buffer_locked(self) -> None:
        """Remove dados antigos do buffer (chamado com _buffer_lock adquirido)."""
        target = MAX_BUFFER_SAMPLES // 2  # Mantém metade
        if self._total_samples <= target:
            return

        if self._audio_chunks:
            full_audio = np.concatenate(self._audio_chunks)
            keep_start = len(full_audio) - target
            self._audio_chunks = [full_audio[keep_start:]]
            self._total_samples = len(self._audio_chunks[0])
            self._chunk_start_sample = max(0, self._chunk_start_sample - keep_start)

    # =========================================================================
    # Worker de transcrição (roda em thread pool)
    # =========================================================================

    def _do_transcribe(
        self,
        audio_chunk: np.ndarray,
        context_prompt: str,
        chunk_id: int,
    ) -> None:
        """Executa o pipeline completo de transcrição de um chunk.

        Roda em thread pool, independentemente do loop de captura de áudio.
        Não bloqueia a captura de novos chunks.

        Pipeline:
            1. Aprimora o áudio (enhance_audio_for_whisper)
            2. Transcreve com Whisper (transcribe_numpy)
            3. Limpa o texto (clean_transcription)
            4. Aplica vocab pessoal (personal_vocab.apply_corrections)
            5. Atualiza contexto para o próximo chunk
            6. Notifica via on_chunk_text callback em ordem

        Args:
            audio_chunk: Array int16 do chunk a transcrever.
            context_prompt: Últimas palavras do chunk anterior (para continuidade).
            chunk_id: Identificador sequencial do chunk (para logging).
        """
        cleaned = ""
        try:
            if self._cancel_requested.is_set():
                return
            # ---- 1. Aprimoramento de áudio -----------------------------------
            apply_enhance = bool(getattr(self.config, "audio_enhance", True))
            profile = getattr(self.config, "audio_enhance_profile", "balanced")
            try:
                from .audio_enhancer import enhance_audio_for_whisper
                if apply_enhance:
                    audio_float = enhance_audio_for_whisper(audio_chunk, profile=profile)
                else:
                    audio_float = audio_chunk.astype(np.float32) / 32768.0
            except Exception as e:
                logger.warning(f"[Chunk #{chunk_id}] Enhancer falhou: {e}. Usando áudio bruto.")
                audio_float = audio_chunk.astype(np.float32) / 32768.0

            # ---- 2. Transcrição via Whisper ----------------------------------
            transcriber = self._transcriber
            if transcriber is not None:
                text = transcriber.transcribe_numpy(
                    audio_float,
                    context_prompt=context_prompt,
                )

                if self._cancel_requested.is_set():
                    return

                if text and text.strip():
                    # ---- 3. Limpeza de texto ----------------------------------------
                    from .speech_cleaner import clean_transcription, parse_custom_fillers

                    custom_fillers_str = str(getattr(self.config, "custom_fillers", ""))
                    custom_fillers = parse_custom_fillers(custom_fillers_str) or None

                    cleaned_temp = clean_transcription(
                        text,
                        remove_stutter=bool(getattr(self.config, "remove_stutters", False)),
                        remove_filler_words=bool(getattr(self.config, "remove_fillers", False)),
                        custom_fillers=custom_fillers,
                        literal_mode=bool(getattr(self.config, "literal_mode", True)),
                    )

                    if cleaned_temp:
                        cleaned = cleaned_temp
                        # ---- 4. Vocabulário pessoal ------------------------------------
                        if not bool(getattr(self.config, "literal_mode", True)):
                            try:
                                from .vocab_cache import personal_vocab
                                cleaned = personal_vocab.apply_corrections(cleaned)
                            except Exception as e:
                                logger.warning(f"[Chunk #{chunk_id}] VocabCache falhou: {e}")

                        # ---- 5. Atualiza contexto para o próximo chunk ------------------
                        words = cleaned.split()
                        # Passa as últimas 8 palavras como contexto (suficiente para continuidade)
                        self._context_prompt = " ".join(words[-8:]) if len(words) >= 8 else cleaned
                    else:
                        logger.debug(
                            f"[Chunk #{chunk_id}] Texto descartado pela limpeza "
                            f"(hallucination ou vazio). Original: {text!r}"
                        )
                else:
                    logger.debug(f"[Chunk #{chunk_id}] Whisper retornou vazio.")

        except Exception as e:
            if self._cancel_requested.is_set():
                return
            error_msg = f"Falha no chunk #{chunk_id}: {e}"
            logger.error(f"[StreamTranscriber] {error_msg}", exc_info=True)
            self.on_error(error_msg)
        finally:
            # ---- 6. Acumula e notifica em ordem -------------------------------
            if self._cancel_requested.is_set():
                return
            with self._output_lock:
                self._output_buffer[chunk_id] = cleaned
                # Entrega todos os chunks cuja vez chegou na ordem esperada
                while self._next_output_id in self._output_buffer:
                    ready_text = self._output_buffer.pop(self._next_output_id)
                    self._next_output_id += 1
                    if ready_text:
                        self._accumulated_text.append(ready_text)
                        # Notifica o app.py — o callback é thread-safe via root.after()
                        self.on_chunk_text(ready_text)

            if cleaned:
                logger.debug(
                    f"[Chunk #{chunk_id}] Transcrito: {cleaned[:60]!r}"
                    f"{'...' if len(cleaned) > 60 else ''}"
                )
