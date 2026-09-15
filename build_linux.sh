#!/bin/bash
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

if [ ! -x ".venv-linux/bin/python" ]; then
    echo "Criando ambiente .venv-linux..."
    python3 -m venv --copies .venv-linux
fi

.venv-linux/bin/python -m pip install --require-hashes -r requirements-build-linux.lock
.venv-linux/bin/python -m pip check

echo "=== Gerando executável do QuantumScribe para Linux ==="
.venv-linux/bin/python -m PyInstaller --clean --noconfirm QuantumScribe-Linux.spec

echo "=== Reduzindo binários de terceiros ==="
for dir in \
    _internal/ctranslate2 \
    _internal/ctranslate2.libs \
    _internal/numpy \
    _internal/numpy.libs \
    _internal/av \
    _internal/av.libs \
    _internal/PIL \
    _internal/pillow.libs \
    _internal/tokenizers \
    _internal/faster_whisper; do
    if [ -d "dist/QuantumScribe/$dir" ]; then
        find "dist/QuantumScribe/$dir" -type f \
            \( -name '*.so' -o -name '*.so.*' \) \
            -exec strip --strip-unneeded {} +
    fi
done

if [ -d "dist/QuantumScribe/_internal" ]; then
    find dist/QuantumScribe/_internal -maxdepth 1 -type f \
        \( -name 'libpython*.so' -o -name 'libpython*.so.*' \) \
        -exec strip --strip-unneeded {} +
fi

echo "=== Removendo codecs de vídeo opcionais do PyAV ==="
if [ -d "dist/QuantumScribe/_internal/av.libs" ]; then
    for pattern in \
        'libx265-*' \
        'libSvtAv1Enc-*' \
        'libx264-*' \
        'libvpx-*' \
        'libdav1d-*' \
        'libswscale-*' \
        'libwebp-*' \
        'libwebpmux-*' \
        'libvpl-*' \
        'libavdevice-*' \
        'libdrm-*'; do
        find dist/QuantumScribe/_internal/av.libs -maxdepth 1 -type f \
            -name "$pattern" -delete
    done
fi

.venv-linux/bin/python scripts/inventory_bundle.py dist/QuantumScribe \
    --output dist/QuantumScribe-inventory.json --max-bytes 262144000

echo ""
echo "Executável gerado com sucesso em: dist/QuantumScribe/QuantumScribe"
