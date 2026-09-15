"""Gera um inventário determinístico e aplica a política do artefato Core.

O relatório não contém timestamps nem caminhos absolutos para que o mesmo
artefato produza o mesmo JSON em máquinas diferentes. O processo de release
usa o código de saída: zero significa que a política foi respeitada.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

DEFAULT_MAX_BYTES = 250 * 1024 * 1024
FORBIDDEN_TOKENS = (
    "nvidia",
    "torch",
    "torchaudio",
    "silero_vad",
    "silero-vad",
    "onnxruntime",
    "noisereduce",
    "scipy",
    "matplotlib",
)
FORBIDDEN_SUFFIXES = (".onnx", ".safetensors", ".pt", ".pth")
FORBIDDEN_MODEL_NAMES = {"model.bin", "model.pt", "model.pth"}


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _forbidden_reasons(relative_path: str) -> list[str]:
    normalized = relative_path.lower()
    reasons = []
    for token in FORBIDDEN_TOKENS:
        if token == "scipy":
            # NumPy wheels can contain a BLAS binary named libscipy_openblas;
            # this is not the SciPy package and must not create a false alarm.
            markers = ("/scipy/", "/scipy.libs/", "scipy-", "scipy/")
            if not any(marker in normalized for marker in markers):
                continue
        if token in normalized:
            reasons.append(token)
    name = Path(normalized).name
    if name in FORBIDDEN_MODEL_NAMES:
        reasons.append("model-file")
    if normalized.endswith(FORBIDDEN_SUFFIXES):
        reasons.append("model-extension")
    return sorted(set(reasons))


def _symlink_digest(target: str) -> str:
    """Hash the link metadata without following the link target."""
    return hashlib.sha256(f"symlink:{target}".encode("utf-8", "surrogateescape")).hexdigest()


def build_inventory(root: Path, *, max_bytes: int, excluded: set[Path] | None = None) -> dict:
    root = root.resolve()
    excluded = {path.resolve() for path in (excluded or set())}
    files: list[dict[str, object]] = []
    forbidden: list[dict[str, object]] = []
    total_bytes = 0

    for path in sorted(
        (item for item in root.rglob("*") if item.is_file() or item.is_symlink()),
        key=lambda item: _relative(item, root),
    ):
        resolved = path.resolve()
        if resolved in excluded:
            continue
        relative = _relative(path, root)
        if path.is_symlink():
            target = os.readlink(path)
            entry = {
                "path": relative,
                "bytes": 0,
                "sha256": _symlink_digest(target),
                "type": "symlink",
                "target": target,
            }
            if not resolved.is_relative_to(root):
                forbidden.append({"path": relative, "reasons": ["symlink-outside-root"]})
        else:
            digest = hashlib.sha256()
            size = 0
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    size += len(chunk)
                    digest.update(chunk)
            entry = {"path": relative, "bytes": size, "sha256": digest.hexdigest()}
        files.append(entry)
        total_bytes += int(entry["bytes"])
        reasons = _forbidden_reasons(relative)
        if reasons:
            forbidden.append({"path": relative, "reasons": reasons})

    return {
        "schema": 1,
        "artifact": root.name,
        "file_count": len(files),
        "total_bytes": total_bytes,
        "total_megabytes": round(total_bytes / (1024 * 1024), 3),
        "policy": {
            "max_bytes": max_bytes,
            "forbidden_tokens": list(FORBIDDEN_TOKENS),
            "passed": total_bytes <= max_bytes and not forbidden,
        },
        "forbidden_matches": forbidden,
        "files": files,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="Diretório do artefato a inventariar")
    parser.add_argument("--output", type=Path, required=True, help="Caminho do relatório JSON")
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    args = parser.parse_args(argv)

    root = args.root.resolve()
    if not root.is_dir():
        parser.error(f"diretório do artefato não encontrado: {root}")
    if args.max_bytes <= 0:
        parser.error("--max-bytes precisa ser positivo")

    output = args.output.resolve()
    inventory = build_inventory(root, max_bytes=args.max_bytes, excluded={output})
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if not inventory["policy"]["passed"]:
        print(
            f"Inventário reprovado: {inventory['total_megabytes']} MB, "
            f"{len(inventory['forbidden_matches'])} violações.",
            file=sys.stderr,
        )
        return 1

    print(
        f"Inventário aprovado: {inventory['total_megabytes']} MB, "
        f"{inventory['file_count']} arquivos."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
