"""Módulo de Gerenciamento de Configurações do LocalWhisper.

Este módulo define a estrutura de dados das configurações do usuário,
gerencia o diretório de dados em %LOCALAPPDATA% e manipula a persistência
do arquivo config.json.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path

# Nome global da aplicação para fins de caminhos no sistema operacional
APP_NAME = "QuantumScribe"
HUD_THEME_IDS = frozenset({"atom_centered", "liquid_orb", "prismatic_bubble"})


@dataclass(slots=True)
class AppConfig:
    """Dataclass que mapeia todas as opções de configuração do aplicativo."""
    model: str = "medium"           # Padrão Pro; instalado somente após consentimento do usuário
    effective_model: str = ""      # Modelo efetivo da sessão (normalmente igual a model)
    language: str = "pt"           # Idioma da transcrição ('pt' para português ou vazio para auto)
    device: str = "auto"           # Detecta CUDA automaticamente e recua preventivamente para CPU
    compute_type: str = "auto"     # Seleciona uma precisão suportada pelo dispositivo efetivo
    preload_model: bool = False    # Carregar sob demanda para manter inicialização e bandeja responsivas
    auto_download_model: bool = False  # Compatibilidade: downloads silenciosos permanecem desativados
    start_with_windows: bool = False  # Inicia automaticamente para a conta atual do Windows
    auto_paste: bool = True        # Insere automaticamente o texto no local focado após a transcrição
    hotkey: str = "Ctrl+Space"     # Atalho de teclado global para iniciar/parar gravação
    initial_prompt: str = (
        "Transcrição em português do Brasil coloquial. "
        "Preservar exatamente: né, tá, pra, pro, tô, aí, sóque, tô, mano, cara. "
        "Termos técnicos de IA: prompt, storyboard, POV, UGC, lip sync, character sheet, product sheet, 16x9, 9x16, beam size. "
        "Marcas e produtos: Knul,X, Nanobanana, Google Flow, TikTok, Cloudflare, WhatsApp, PIX, ChatGPT, Pinterest. "
        "Termos de produto: chuteira, solado, logo, consistência, amadora, amadoras. "
        "Demais: OK, e-mail, Docker, GitHub, HTML, JSON, CSS, cron job, cron jobs, AnyDesk."
    )
    play_sounds: bool = True       # Reproduz efeitos sonoros ao iniciar e finalizar gravação/transcrição
    sound_volume: float = 0.5      # Volume dos efeitos sonoros (0.0 a 1.0)
    hud_theme: str = "atom_centered" # Tema padrão: átomo centralizado e compacto
    atom_color: str = "#BF5AF2"    # Cor padrão do átomo: violeta Quantum
    theme_mode: str = "dark"       # Aparência da interface: "dark" (escuro) ou "light" (claro)
    accent_color: str = "#BF5AF2"  # Cor de destaque da interface; padrão violeta Quantum
    hotkey_translate: str = "Ctrl+Alt+Space"  # Atalho para ditar e traduzir para o inglês
    hotkey_auto_send: str = "Ctrl+Shift+Space"  # Atalho para ditar, colar e enviar automático (Enter)
    audio_device: str = ""         # Nome do dispositivo de entrada de áudio (microfone)
    custom_dict: dict[str, str] = field(default_factory=dict) # Dicionário para Find & Replace inteligente (Erro -> Acerto)
    tone_style: str = "natural"    # Estilo do tom (natural, formal, developer)
    literal_mode: bool = True      # Preserva as palavras do Whisper sem reescrita/correção automática
    punctuation_assist: bool = True # Melhora apenas a pontuação, sem modificar palavras
    punctuation_pause_ms: int = 650 # Pausa mínima entre segmentos para inserir limite de frase
    continuous_learning: bool = False # Extrair vocabulário ativo do diário (desligado no modo literal)
    use_llm_rewriter: bool = False # Usar Mini-LLM local para pós-processamento
    llm_model_repo: str = "jncraton/Qwen2.5-0.5B-Instruct-ct2-int8" # Repositório HF do modelo CTranslate2
    ai_mode: bool = False  # Reservado: reformulação como comando IA (não implementado)
    custom_tones: dict[str, str] = field(default_factory=dict) # Armazenar edições e novos tons
    llm_custom_tones: dict[str, str] = field(default_factory=dict) # Tons customizados para a LLM
    # ---- Motor de Streaming (stream_transcriber.py) ----
    streaming_mode: bool = False          # Ativa transcrição streaming contínua por chunks
    stream_chunk_seconds: float = 5.0     # Tamanho alvo do chunk de streaming em segundos
    stream_min_silence_ms: int = 350      # Silêncio mínimo (ms) para cortar chunk no VAD
    audio_enhance: bool = True            # Aprimoramento de áudio (filtro + noisereduce + normalização)
    audio_enhance_profile: str = "balanced" # Perfil de aprimoramento: fast, balanced, quality
    remove_stutters: bool = False         # Remove repetições de palavras; desligado para preservar o que foi falado
    remove_fillers: bool = False          # Remove fillers (hmm, ãh, etc.) do texto transcrito
    custom_fillers: str = ""              # Fillers personalizados separados por vírgula
    save_audio_for_training: bool = False  # Reservado: coleta de dataset (não implementado)
    max_recording_seconds: int = 600      # Limite máximo de gravação clássica em segundos (10 minutos)

    # ---- Quantum Brain ----
    hotkey_quantum_brain: str = "Ctrl+Shift+D"   # Atalho para ditar e salvar no Quantum Brain
    quantum_brain_enabled: bool = True             # Habilita o Quantum Brain
    quantum_brain_llm_repo: str = "jncraton/Qwen2.5-3B-Instruct-ct2-int8"  # Modelo via CTranslate2
    quantum_brain_sync_interval_min: int = 30      # Intervalo (minutos) entre sínteses automáticas
    quantum_brain_sync_threshold: int = 5          # Nº de notas brutas para acionar síntese imediata
    quantum_brain_also_paste: bool = True          # Também cola o texto no cursor (como o modo normal)
    quantum_brain_api_key: str = ""               # Reservado para futura integração cloud
    setup_prompt_dismissed_signature: str = ""     # Não repetir a mesma oferta de preparação a cada abertura

    def __post_init__(self) -> None:
        """Normaliza a configuração quando ela nasce em memória."""
        self.normalize()

    def normalize(self) -> None:
        """Preserva invariantes mesmo quando uma opção muda após a construção.

        A tela de ajustes aplica mudanças na mesma instância de ``AppConfig``. Por
        isso, deixar esta regra apenas no ``__post_init__`` permitiria persistir
        combinações que a promessa de Transcrição Literal proíbe.
        """
        if not self.effective_model:
            self.effective_model = self.model
        if self.hud_theme not in HUD_THEME_IDS:
            self.hud_theme = "atom_centered"
        # Modo literal é uma promessa de não alterar o texto reconhecido. Também
        # normalizamos configurações antigas que possam ter combinações inválidas.
        if self.literal_mode:
            self.remove_stutters = False
            self.remove_fillers = False
            self.continuous_learning = False
            self.use_llm_rewriter = False


def app_data_dir() -> Path:
    """Retorna o diretório base para salvar arquivos locais do aplicativo.

    No Windows, geralmente aponta para %LOCALAPPDATA%\\QuantumScribe.
    No Linux, aponta para $XDG_DATA_HOME/QuantumScribe ou ~/.local/share/QuantumScribe.
    """
    import sys
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home()))
    else:
        xdg_data = os.environ.get("XDG_DATA_HOME")
        base = Path(xdg_data) if xdg_data else Path.home() / ".local" / "share"
    path = base / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def config_path() -> Path:
    """Retorna o caminho absoluto do arquivo config.json."""
    return app_data_dir() / "config.json"


def model_dir() -> Path:
    """Retorna o diretório onde os modelos Whisper baixados serão salvos."""
    path = app_data_dir() / "models"
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_config() -> AppConfig:
    """Carrega as configurações a partir do arquivo config.json.

    Caso o arquivo não exista ou esteja corrompido, cria um novo com os
    valores padrões definidos na classe AppConfig.
    """
    path = config_path()
    if not path.exists():
        config = AppConfig()
        save_config(config)
        return config

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))

        # Patch automático para repositório do LLM obsoleto (quebrado no HF)
        if raw.get("llm_model_repo") == "michaelfeil/ct2fast-Qwen1.5-0.5B-Chat":
            raw["llm_model_repo"] = "jncraton/Qwen2.5-0.5B-Instruct-ct2-int8"

        # O modelo escolhido continua sendo o efetivo mesmo quando ainda não foi baixado.
        # A instalação exige uma ação explícita na preparação inicial ou nas configurações.
        configured_model = raw.get("model", AppConfig.__dataclass_fields__["model"].default)
        raw["effective_model"] = configured_model

        # Corrige initial_prompt com encoding quebrado (contém \uFFFD = leitura corrompida)
        stored_prompt = raw.get("initial_prompt", "")
        if stored_prompt and "\ufffd" in stored_prompt:
            raw["initial_prompt"] = AppConfig.__dataclass_fields__["initial_prompt"].default

        # Patch automático: atualiza o initial_prompt antigo (curto e genérico) para o novo
        # rico em vocabulário do nicho. Detecta pelo prefixo característico do prompt antigo.
        stored_prompt = raw.get("initial_prompt", "")
        _OLD_PROMPT_PREFIX = "Olá. Transcreva em português"
        if stored_prompt.startswith(_OLD_PROMPT_PREFIX) or "Canuxis" in stored_prompt or "Canuxias" in stored_prompt:
            raw["initial_prompt"] = AppConfig.__dataclass_fields__["initial_prompt"].default

        allowed = AppConfig.__dataclass_fields__.keys()
        # Filtra apenas os parâmetros válidos permitidos para evitar erros de inicialização
        return AppConfig(**{key: value for key, value in raw.items() if key in allowed})
    except (OSError, ValueError, TypeError):
        config = AppConfig()
        try:
            save_config(config)
        except OSError:
            pass
        return config


def save_config(config: AppConfig) -> None:
    """Salva a estrutura AppConfig de volta no formato JSON.

    Args:
        config: Instância das configurações a serem escritas.
    """
    # A instância pode ter sido alterada diretamente pela interface desde sua
    # criação; normalize antes de persistir qualquer combinação incompatível.
    config.normalize()
    data = asdict(config)
    data.pop("effective_model", None)
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            json.dump(data, temporary, ensure_ascii=False, indent=2)
            temporary.write("\n")
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def is_model_downloaded(model_name: str) -> bool:
    """Retorna ``True`` somente quando o snapshot possui os arquivos essenciais."""
    return _has_complete_model_snapshot(model_dir(), model_name)


def model_snapshot_path(model_name: str) -> Path:
    """Retorna um snapshot local completo para impedir resolução de rede no carregamento."""
    snapshots_dir = model_dir() / f"models--Systran--faster-whisper-{model_name}" / "snapshots"
    required_files = ("config.json", "model.bin", "tokenizer.json")
    try:
        candidates = sorted(
            (
                snapshot
                for snapshot in snapshots_dir.iterdir()
                if snapshot.is_dir()
                and all((snapshot / name).is_file() and (snapshot / name).stat().st_size > 0 for name in required_files)
            ),
            key=lambda snapshot: snapshot.stat().st_mtime,
            reverse=True,
        )
    except OSError:
        candidates = []
    if not candidates:
        raise FileNotFoundError(f"Snapshot completo do modelo {model_name!r} não encontrado")
    return candidates[0]


def _has_complete_model_snapshot(models_path: Path, model_name: str) -> bool:
    """Evita tratar downloads parciais do Hugging Face como modelos utilizáveis."""
    snapshots_dir = (
        models_path
        / f"models--Systran--faster-whisper-{model_name}"
        / "snapshots"
    )
    if not snapshots_dir.is_dir():
        return False

    required_files = ("config.json", "model.bin", "tokenizer.json")
    try:
        for snapshot in snapshots_dir.iterdir():
            if not snapshot.is_dir():
                continue
            if all((snapshot / filename).is_file() for filename in required_files):
                # Um link quebrado ou um arquivo vazio também representa download incompleto.
                if all((snapshot / filename).stat().st_size > 0 for filename in required_files):
                    return True
    except OSError:
        return False
    return False


def migrate_legacy_data() -> None:
    """Migra dados do diretório legado LocalWhisper para QuantumScribe, se necessário.

    Executada uma única vez na primeira inicialização após o rebrand.
    Copia config, diary e outros arquivos pequenos sem copiar a pasta de modelos pesada.
    """
    import shutil
    base = Path(os.environ.get("LOCALAPPDATA", Path.home()))
    legacy_dir = base / "LocalWhisper"
    new_dir = base / "QuantumScribe"

    # Pastas e arquivos a NÃO migrar (muito grandes ou irrelevantes)
    SKIP_ITEMS = {"models", "app.log", "emergency_audio.wav", "__pycache__"}

    # Só migra se o diretório legado existe e o novo está vazio (primeira execução)
    if not legacy_dir.is_dir():
        return
    if new_dir.is_dir() and any(new_dir.iterdir()):
        return  # Já migrado ou o usuário já tem dados no novo diretório

    try:
        new_dir.mkdir(parents=True, exist_ok=True)
        for item in legacy_dir.iterdir():
            if item.name in SKIP_ITEMS:
                continue
            dest = new_dir / item.name
            if not dest.exists():
                if item.is_dir():
                    shutil.copytree(str(item), str(dest))
                else:
                    shutil.copy2(str(item), str(dest))
        print("[Quantum Scribe] Migração de dados LocalWhisper → QuantumScribe concluída (sem modelos).")
    except Exception as e:
        print(f"[Quantum Scribe] Aviso: falha na migração de dados: {e}")
