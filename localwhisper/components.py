"""Instala componentes opcionais assinados por hash, sem executar instaladores externos."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Callable, Iterable

from . import __version__
from .config import app_data_dir

_RELEASE_BASE = "https://github.com/thebuzuzu/QuantumScribe/releases/download"
_ALLOWED_DOWNLOAD_HOSTS = {
    "github.com",
    "objects.githubusercontent.com",
    "release-assets.githubusercontent.com",
}
_MAX_CHECKSUM_BYTES = 1024 * 1024


@dataclass(frozen=True, slots=True)
class ComponentSpec:
    key: str
    asset_name: str
    required_files: tuple[str, ...]
    max_download_bytes: int
    max_uncompressed_bytes: int
    restart_required: bool


def _specs(version: str = __version__) -> dict[str, ComponentSpec]:
    return {
        "cuda": ComponentSpec(
            key="cuda",
            asset_name=f"QuantumScribe-CUDA-{version}-Windows-x64.zip",
            required_files=(
                "nvidia/cublas/bin/cublas64_12.dll",
                "nvidia/cublas/bin/cublasLt64_12.dll",
                "nvidia/cudnn/bin/cudnn64_9.dll",
            ),
            max_download_bytes=900 * 1024 * 1024,
            max_uncompressed_bytes=1400 * 1024 * 1024,
            restart_required=True,
        ),
        "silero_vad": ComponentSpec(
            key="silero_vad",
            asset_name=f"QuantumScribe-SileroVAD-{version}-Windows-x64.zip",
            required_files=("silero_vad.onnx",),
            max_download_bytes=12 * 1024 * 1024,
            max_uncompressed_bytes=16 * 1024 * 1024,
            restart_required=False,
        ),
    }


def component_dir(key: str, version: str = __version__) -> Path:
    if key not in _specs(version):
        raise ValueError(f"Componente desconhecido: {key}")
    return app_data_dir() / "components" / key / version


def component_installed(key: str, version: str = __version__) -> bool:
    return compatible_component_root(key, version) is not None


def _valid_component_root(key: str, root: Path, version: str) -> bool:
    spec = _specs(version)[key]
    marker = root / "component.json"
    if not marker.is_file():
        return False
    try:
        data = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return (
        data.get("key") == key
        and data.get("version") == root.name
        and all((root / relative).is_file() for relative in spec.required_files)
    )


def compatible_component_root(key: str, version: str = __version__) -> Path | None:
    """Reutiliza componentes verificados entre patches da mesma linha major.minor."""
    requested = tuple(int(part) for part in version.split("."))
    exact = component_dir(key, version)
    if _valid_component_root(key, exact, version):
        return exact

    parent = exact.parent
    try:
        candidates = []
        for root in parent.iterdir():
            try:
                candidate = tuple(int(part) for part in root.name.split("."))
            except ValueError:
                continue
            if len(candidate) == 3 and candidate[:2] == requested[:2]:
                candidates.append((candidate, root))
    except OSError:
        return None
    for _candidate, root in sorted(candidates, reverse=True):
        if _valid_component_root(key, root, version):
            return root
    return None


def nvidia_gpu_detected() -> tuple[bool, str]:
    """Detecta GPU NVIDIA sem exigir que cuBLAS/cuDNN já estejam instalados."""
    try:
        import ctranslate2

        if ctranslate2.get_cuda_device_count() > 0:
            return True, "GPU NVIDIA detectada pelo CTranslate2"
    except Exception:
        pass

    if sys.platform == "win32":
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                check=False,
                capture_output=True,
                text=True,
                timeout=4,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            name = next((line.strip() for line in result.stdout.splitlines() if line.strip()), "")
            if result.returncode == 0 and name:
                return True, name
        except (OSError, subprocess.SubprocessError):
            pass
    return False, "nenhuma GPU NVIDIA compatível foi detectada"


def _read_url(url: str, max_bytes: int) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": f"QuantumScribe/{__version__}"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            final_host = (urllib.parse.urlparse(response.geturl()).hostname or "").lower()
            if final_host not in _ALLOWED_DOWNLOAD_HOSTS:
                raise RuntimeError(f"Download redirecionado para host não autorizado: {final_host}")
            declared = response.headers.get("Content-Length")
            if declared and int(declared) > max_bytes:
                raise RuntimeError("Download excede o tamanho máximo permitido")
            data = response.read(max_bytes + 1)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            raise RuntimeError(
                "Os componentes opcionais desta versão ainda não estão disponíveis."
            ) from error
        raise RuntimeError("Não foi possível consultar os componentes opcionais.") from error
    except urllib.error.URLError as error:
        raise RuntimeError("Não foi possível acessar os componentes opcionais.") from error
    if len(data) > max_bytes:
        raise RuntimeError("Download excede o tamanho máximo permitido")
    return data


def component_release_available(key: str, version: str = __version__) -> bool:
    """Confirma silenciosamente que a release publicou o componente antes de oferecê-lo."""
    spec = _specs(version)[key]
    release_url = f"{_RELEASE_BASE}/v{version}"
    try:
        checksums = _read_url(f"{release_url}/SHA256SUMS.txt", _MAX_CHECKSUM_BYTES)
        _expected_hash(checksums, spec.asset_name)
    except (OSError, RuntimeError):
        return False
    return True


def _download_url(url: str, destination: Path, max_bytes: int) -> None:
    """Transfere arquivos grandes em streaming para não ocupar centenas de MB de RAM."""
    request = urllib.request.Request(url, headers={"User-Agent": f"QuantumScribe/{__version__}"})
    total = 0
    with urllib.request.urlopen(request, timeout=30) as response:
        final_host = (urllib.parse.urlparse(response.geturl()).hostname or "").lower()
        if final_host not in _ALLOWED_DOWNLOAD_HOSTS:
            raise RuntimeError(f"Download redirecionado para host não autorizado: {final_host}")
        declared = response.headers.get("Content-Length")
        if declared and int(declared) > max_bytes:
            raise RuntimeError("Download excede o tamanho máximo permitido")
        with destination.open("wb") as output:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    raise RuntimeError("Download excede o tamanho máximo permitido")
                output.write(chunk)


def _expected_hash(checksums: bytes, asset_name: str) -> str:
    try:
        text = checksums.decode("ascii")
    except UnicodeDecodeError as error:
        raise RuntimeError("Arquivo de checksums inválido") from error
    for line in text.splitlines():
        parts = line.strip().split(maxsplit=1)
        if len(parts) != 2:
            continue
        digest, filename = parts[0].lower(), parts[1].lstrip("* ")
        if filename == asset_name and len(digest) == 64 and all(c in "0123456789abcdef" for c in digest):
            return digest
    raise RuntimeError(f"Checksum SHA-256 não publicado para {asset_name}")


def verify_sha256(path: Path, expected: str) -> None:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest().lower() != expected.lower():
        raise RuntimeError("O componente baixado falhou na verificação SHA-256")


def _safe_extract_zip(archive: Path, destination: Path, max_uncompressed_bytes: int) -> None:
    destination = destination.resolve()
    total = 0
    with zipfile.ZipFile(archive) as bundle:
        entries = bundle.infolist()
        if len(entries) > 500:
            raise RuntimeError("Componente contém arquivos demais")
        for entry in entries:
            relative = PurePosixPath(entry.filename)
            if relative.is_absolute() or ".." in relative.parts or not relative.parts:
                raise RuntimeError("Componente contém caminho inseguro")
            if entry.flag_bits & 0x1:
                raise RuntimeError("Componentes criptografados não são aceitos")
            unix_mode = (entry.external_attr >> 16) & 0o170000
            if unix_mode == 0o120000:
                raise RuntimeError("Links simbólicos não são aceitos em componentes")
            total += entry.file_size
            if total > max_uncompressed_bytes:
                raise RuntimeError("Componente descompactado excede o limite permitido")
            target = destination.joinpath(*relative.parts).resolve()
            if os.path.commonpath((str(destination), str(target))) != str(destination):
                raise RuntimeError("Componente tentou sair do diretório isolado")
            if entry.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with bundle.open(entry) as source, target.open("wb") as output:
                shutil.copyfileobj(source, output, length=1024 * 1024)


def install_component(
    key: str,
    *,
    version: str = __version__,
    on_status: Callable[[str], None] | None = None,
) -> Path:
    """Baixa um ZIP da release correspondente, valida e instala de forma atômica."""
    spec = _specs(version)[key]
    installed_root = compatible_component_root(key, version)
    if installed_root is not None:
        return installed_root

    status = on_status or (lambda _message: None)
    release_url = f"{_RELEASE_BASE}/v{version}"
    status("Verificando assinatura SHA-256...")
    checksums = _read_url(f"{release_url}/SHA256SUMS.txt", _MAX_CHECKSUM_BYTES)
    expected = _expected_hash(checksums, spec.asset_name)

    components_root = app_data_dir() / "components"
    components_root.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f"{key}-", suffix=".zip.part", dir=components_root)
    os.close(fd)
    archive = Path(temp_name)
    staging = Path(tempfile.mkdtemp(prefix=f"{key}-staging-", dir=components_root))
    try:
        status(f"Baixando {spec.asset_name}...")
        _download_url(f"{release_url}/{spec.asset_name}", archive, spec.max_download_bytes)
        verify_sha256(archive, expected)
        status("Validando e instalando o componente...")
        _safe_extract_zip(archive, staging, spec.max_uncompressed_bytes)
        missing = [name for name in spec.required_files if not (staging / name).is_file()]
        if missing:
            raise RuntimeError(f"Componente incompleto; arquivos ausentes: {', '.join(missing)}")
        (staging / "component.json").write_text(
            json.dumps({"key": key, "version": version, "sha256": expected}, indent=2),
            encoding="utf-8",
        )

        destination = component_dir(key, version)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            shutil.rmtree(destination)
        os.replace(staging, destination)
        status("Componente instalado e verificado.")
        return destination
    finally:
        archive.unlink(missing_ok=True)
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)


def installed_component_roots(keys: Iterable[str] = ("cuda",)) -> tuple[Path, ...]:
    return tuple(
        root
        for key in keys
        if (root := compatible_component_root(key)) is not None
    )
