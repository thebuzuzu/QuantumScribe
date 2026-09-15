import hashlib
import io
import json

import pytest

from localwhisper import updater


class _FakeResponse(io.BytesIO):
    def __init__(self, data: bytes, url: str):
        super().__init__(data)
        self.headers = {"Content-Length": str(len(data))}
        self._url = url

    def geturl(self):
        return self._url

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()


def _release(version: str, installer_size: int) -> bytes:
    installer_name = f"QuantumScribe-Setup-{version}-Windows-x64.exe"
    linux_name = f"QuantumScribe-Core-{version}-Linux-x64.tar.gz"
    return json.dumps(
        {
            "tag_name": f"v{version}",
            "draft": False,
            "prerelease": False,
            "html_url": f"https://github.com/thebuzuzu/QuantumScribe/releases/tag/v{version}",
            "assets": [
                {
                    "name": installer_name,
                    "size": installer_size,
                    "browser_download_url": f"https://github.com/thebuzuzu/QuantumScribe/releases/download/v{version}/{installer_name}",
                },
                {
                    "name": linux_name,
                    "size": installer_size,
                    "browser_download_url": f"https://github.com/thebuzuzu/QuantumScribe/releases/download/v{version}/{linux_name}",
                },
                {
                    "name": "SHA256SUMS.txt",
                    "size": 100,
                    "browser_download_url": f"https://github.com/thebuzuzu/QuantumScribe/releases/download/v{version}/SHA256SUMS.txt",
                },
            ],
        }
    ).encode()


def test_update_check_ignores_same_or_older_release(monkeypatch):
    payload = _release("2.2.11", 10 * 1024 * 1024)
    monkeypatch.setattr(updater, "_read_url", lambda *_args: payload)
    monkeypatch.setattr(updater.sys, "platform", "win32")

    assert updater.check_for_update("2.2.11") is None
    assert updater.check_for_update("2.2.12") is None


def test_update_check_requires_exact_official_assets(monkeypatch):
    payload = _release("2.2.13", 10 * 1024 * 1024)
    monkeypatch.setattr(updater, "_read_url", lambda *_args: payload)
    monkeypatch.setattr(updater.sys, "platform", "win32")

    info = updater.check_for_update("2.2.12")

    assert info is not None
    assert info.version == "2.2.13"
    assert info.installer.name == "QuantumScribe-Setup-2.2.13-Windows-x64.exe"


def test_update_check_rejects_unofficial_asset_url(monkeypatch):
    payload = json.loads(_release("2.2.13", 10 * 1024 * 1024))
    payload["assets"][0]["browser_download_url"] = "https://example.invalid/setup.exe"
    monkeypatch.setattr(updater, "_read_url", lambda *_args: json.dumps(payload).encode())
    monkeypatch.setattr(updater.sys, "platform", "win32")

    with pytest.raises(updater.UpdateError, match="não autorizado"):
        updater.check_for_update("2.2.12")


def test_update_check_selects_official_linux_package(monkeypatch):
    payload = _release("2.2.13", 10 * 1024 * 1024)
    monkeypatch.setattr(updater, "_read_url", lambda *_args: payload)
    monkeypatch.setattr(updater.sys, "platform", "linux")

    info = updater.check_for_update("2.2.12")

    assert info is not None
    assert info.installer.name == "QuantumScribe-Core-2.2.13-Linux-x64.tar.gz"


def test_download_rejects_modified_installer(tmp_path, monkeypatch):
    payload = b"instalador adulterado"
    original_hash = hashlib.sha256(b"instalador oficial").hexdigest()
    name = "QuantumScribe-Setup-2.2.13-Windows-x64.exe"
    info = updater.UpdateInfo(
        "2.2.13",
        "https://github.com/thebuzuzu/QuantumScribe/releases/tag/v2.2.13",
        updater.ReleaseAsset(
            name,
            f"https://github.com/thebuzuzu/QuantumScribe/releases/download/v2.2.13/{name}",
            len(payload),
        ),
        updater.ReleaseAsset(
            "SHA256SUMS.txt",
            "https://github.com/thebuzuzu/QuantumScribe/releases/download/v2.2.13/SHA256SUMS.txt",
            100,
        ),
    )
    monkeypatch.setattr(updater, "app_data_dir", lambda: tmp_path)
    monkeypatch.setattr(updater, "_read_url", lambda *_args: f"{original_hash}  {name}\n".encode())
    monkeypatch.setattr(
        updater.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: _FakeResponse(
            payload, "https://release-assets.githubusercontent.com/setup.exe"
        ),
    )

    with pytest.raises(updater.UpdateError, match="SHA-256"):
        updater.download_update(info)
    assert not list(tmp_path.rglob("*.exe"))


def test_download_accepts_matching_hash_and_reports_progress(tmp_path, monkeypatch):
    payload = b"instalador oficial"
    digest = hashlib.sha256(payload).hexdigest()
    name = "QuantumScribe-Setup-2.2.13-Windows-x64.exe"
    info = updater.UpdateInfo(
        "2.2.13",
        "https://github.com/thebuzuzu/QuantumScribe/releases/tag/v2.2.13",
        updater.ReleaseAsset(
            name,
            f"https://github.com/thebuzuzu/QuantumScribe/releases/download/v2.2.13/{name}",
            len(payload),
        ),
        updater.ReleaseAsset(
            "SHA256SUMS.txt",
            "https://github.com/thebuzuzu/QuantumScribe/releases/download/v2.2.13/SHA256SUMS.txt",
            100,
        ),
    )
    monkeypatch.setattr(updater, "app_data_dir", lambda: tmp_path)
    monkeypatch.setattr(updater, "_read_url", lambda *_args: f"{digest}  {name}\n".encode())
    monkeypatch.setattr(
        updater.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: _FakeResponse(
            payload, "https://release-assets.githubusercontent.com/setup.exe"
        ),
    )
    progress = []

    installer, expected = updater.download_update(
        info, lambda received, total: progress.append((received, total))
    )

    assert installer.read_bytes() == payload
    assert expected == digest
    assert progress[-1] == (len(payload), len(payload))


def test_schedule_revalidates_hash_before_starting_helper(tmp_path, monkeypatch):
    installer = tmp_path / "setup.exe"
    installer.write_bytes(b"alterado")
    monkeypatch.setattr(updater.sys, "platform", "win32")

    with pytest.raises(updater.UpdateError, match="SHA-256"):
        updater.schedule_update_after_exit(
            installer, hashlib.sha256(b"original").hexdigest(), 123
        )


def test_schedule_waits_for_app_then_runs_silent_installer(tmp_path, monkeypatch):
    installer = tmp_path / "updates" / "QuantumScribe-Setup-2.2.18-Windows-x64.exe"
    installer.parent.mkdir()
    installer.write_bytes(b"instalador verificado")
    digest = hashlib.sha256(installer.read_bytes()).hexdigest()
    system_root = tmp_path / "Windows"
    powershell = system_root / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
    powershell.parent.mkdir(parents=True)
    powershell.write_bytes(b"powershell")
    local_app_data = tmp_path / "LocalAppData"
    captured = {}

    monkeypatch.setattr(updater.sys, "platform", "win32")
    monkeypatch.setenv("SystemRoot", str(system_root))
    monkeypatch.setenv("LOCALAPPDATA", str(local_app_data))
    monkeypatch.setattr(
        updater.subprocess,
        "Popen",
        lambda args, **kwargs: captured.update(args=args, kwargs=kwargs),
    )
    monkeypatch.setattr(updater.subprocess, "CREATE_NO_WINDOW", 0x08000000, raising=False)
    monkeypatch.setattr(updater.subprocess, "DETACHED_PROCESS", 0x00000008, raising=False)

    updater.schedule_update_after_exit(installer, digest, 456)

    helper_script = installer.parent / "apply-update.ps1"
    script = helper_script.read_text(encoding="utf-8-sig")
    assert "Get-Process -Id 456" in script
    assert "Security.Cryptography.SHA256" in script
    assert "Get-FileHash" not in script
    assert "-ArgumentList '/S'" in script
    assert digest in script
    assert str(local_app_data / "Programs" / "QuantumScribe" / "QuantumScribe.exe") in script
    assert "ProductVersion" in script
    assert "2.2.18" in script
    assert "} finally {" in script
    assert '"error: $($_.Exception.Message)"' in script
    assert captured["args"][-2:] == ["-File", str(helper_script)]
    assert captured["kwargs"]["creationflags"] == 0x08000000
    assert (installer.parent / "update-status.txt").read_text(encoding="utf-8") == "scheduled"


def test_schedule_rejects_unexpected_installer_name(tmp_path, monkeypatch):
    installer = tmp_path / "setup.exe"
    installer.write_bytes(b"instalador verificado")
    digest = hashlib.sha256(installer.read_bytes()).hexdigest()
    monkeypatch.setattr(updater.sys, "platform", "win32")

    with pytest.raises(updater.UpdateError, match="nome do instalador"):
        updater.schedule_update_after_exit(installer, digest, 456)


def test_schedule_linux_revalidates_extracts_safely_and_restarts(tmp_path, monkeypatch):
    package = tmp_path / "updates" / "QuantumScribe-Core-2.2.22-Linux-x64.tar.gz"
    package.parent.mkdir()
    package.write_bytes(b"pacote linux verificado")
    digest = hashlib.sha256(package.read_bytes()).hexdigest()
    captured = {}

    monkeypatch.setattr(updater.sys, "platform", "linux")
    monkeypatch.setattr(updater.shutil, "which", lambda name: "/usr/bin/python3" if name == "python3" else None)
    monkeypatch.setattr(
        updater.subprocess,
        "Popen",
        lambda args, **kwargs: captured.update(args=args, kwargs=kwargs),
    )

    updater.schedule_update_after_exit(package, digest, 789)

    helper_script = package.parent / "apply-update.py"
    script = helper_script.read_text(encoding="utf-8")
    assert "parent_pid = 789" in script
    assert "filter=\"data\"" in script
    assert "O pacote contém um caminho inseguro." in script
    assert "install_linux_shortcut.sh" in script
    assert digest in script
    assert "start_new_session=True" in script
    assert captured["args"] == ["/usr/bin/python3", str(helper_script)]
    assert captured["kwargs"]["start_new_session"] is True
    assert (package.parent / "update-status.txt").read_text(encoding="utf-8") == "scheduled"
