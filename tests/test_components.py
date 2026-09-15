import hashlib
import io
import json
import zipfile

import pytest

from localwhisper import components


def test_component_downloads_follow_the_current_repository() -> None:
    assert components._RELEASE_BASE == "https://github.com/thebuzuzu/QuantumScribe/releases/download"


class _FakeResponse(io.BytesIO):
    def __init__(self, data, url="https://release-assets.githubusercontent.com/component.zip"):
        super().__init__(data)
        self.headers = {"Content-Length": str(len(data))}
        self._url = url

    def geturl(self):
        return self._url

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()


def test_component_marker_requires_every_expected_file(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    root = components.component_dir("silero_vad", "2.2.0")
    root.mkdir(parents=True)
    (root / "component.json").write_text(
        json.dumps({"key": "silero_vad", "version": "2.2.0"}), encoding="utf-8"
    )

    assert components.component_installed("silero_vad", "2.2.0") is False
    (root / "silero_vad.onnx").write_bytes(b"model")
    assert components.component_installed("silero_vad", "2.2.0") is True


def test_component_is_reused_across_patch_versions(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    root = components.component_dir("cuda", "2.2.17")
    for relative in components._specs("2.2.19")["cuda"].required_files:
        (root / relative).parent.mkdir(parents=True, exist_ok=True)
        (root / relative).write_bytes(b"verified")
    (root / "component.json").write_text(
        json.dumps({"key": "cuda", "version": "2.2.17"}), encoding="utf-8"
    )

    assert components.compatible_component_root("cuda", "2.2.19") == root
    assert components.component_installed("cuda", "2.2.19") is True


def test_component_is_not_reused_across_minor_versions(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    root = components.component_dir("silero_vad", "2.1.9")
    root.mkdir(parents=True)
    (root / "silero_vad.onnx").write_bytes(b"verified")
    (root / "component.json").write_text(
        json.dumps({"key": "silero_vad", "version": "2.1.9"}), encoding="utf-8"
    )

    assert components.component_installed("silero_vad", "2.2.0") is False


def test_expected_hash_matches_exact_asset_name():
    wanted = "a" * 64
    checksums = f"{'b' * 64}  prefix-app.zip\n{wanted}  app.zip\n".encode("ascii")

    assert components._expected_hash(checksums, "app.zip") == wanted


def test_verify_sha256_rejects_modified_component(tmp_path):
    archive = tmp_path / "component.zip"
    archive.write_bytes(b"conteudo alterado")

    with pytest.raises(RuntimeError, match="SHA-256"):
        components.verify_sha256(archive, hashlib.sha256(b"original").hexdigest())


def test_large_download_is_streamed_to_disk(tmp_path, monkeypatch):
    payload = b"x" * (2 * 1024 * 1024 + 17)
    monkeypatch.setattr(components.urllib.request, "urlopen", lambda *_args, **_kwargs: _FakeResponse(payload))
    destination = tmp_path / "component.part"

    components._download_url("https://github.com/component.zip", destination, len(payload))

    assert destination.stat().st_size == len(payload)


def test_download_rejects_unapproved_redirect_host(tmp_path, monkeypatch):
    monkeypatch.setattr(
        components.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: _FakeResponse(b"x", "https://example.invalid/component.zip"),
    )

    with pytest.raises(RuntimeError, match="host não autorizado"):
        components._download_url("https://github.com/component.zip", tmp_path / "part", 10)


def test_safe_extract_rejects_zip_traversal(tmp_path):
    archive = tmp_path / "malicious.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("../outside.dll", b"nope")

    with pytest.raises(RuntimeError, match="caminho inseguro"):
        components._safe_extract_zip(archive, tmp_path / "target", 1024)
    assert not (tmp_path / "outside.dll").exists()


def test_safe_extract_accepts_bounded_regular_files(tmp_path):
    archive = tmp_path / "valid.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("nvidia/cublas/bin/cublas64_12.dll", b"verified")

    target = tmp_path / "target"
    components._safe_extract_zip(archive, target, 1024)

    assert (target / "nvidia" / "cublas" / "bin" / "cublas64_12.dll").read_bytes() == b"verified"
