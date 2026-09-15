import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_project_versions_stay_in_sync():
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    init_text = (ROOT / "localwhisper" / "__init__.py").read_text(encoding="utf-8")
    match = re.search(r'__version__\s*=\s*"([^"]+)"', init_text)

    assert match is not None
    assert metadata["project"]["version"] == match.group(1)


def test_changelog_starts_at_runtime_version():
    init_text = (ROOT / "localwhisper" / "__init__.py").read_text(encoding="utf-8")
    version_match = re.search(r'__version__\s*=\s*"([^"]+)"', init_text)
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    heading_match = re.search(r"^## \[([^\]]+)\]", changelog, re.MULTILINE)

    assert version_match is not None
    assert heading_match is not None
    assert heading_match.group(1) == "Não publicado"
    assert re.search(r"^## \[" + re.escape(version_match.group(1)) + r"\]", changelog, re.MULTILINE)


def test_windows_packaging_sources_exist():
    expected = (
        ROOT / "localwhisper" / "assets" / "icon.png",
        ROOT / "QuantumScribe.spec",
        ROOT / "installer" / "QuantumScribe.nsi",
    )

    assert all(path.is_file() for path in expected)


def test_linux_packaging_sources_exist():
    expected = (
        ROOT / "localwhisper" / "assets" / "tray-icon.png",
        ROOT / "QuantumScribe-Linux.spec",
        ROOT / "requirements-linux.txt",
        ROOT / "install_linux.sh",
        ROOT / "install_linux_latest.sh",
        ROOT / "install_linux_shortcut.sh",
        ROOT / "run_linux.sh",
        ROOT / "build_linux.sh",
    )

    assert all(path.is_file() for path in expected)
    build_script = (ROOT / "build_linux.sh").read_text(encoding="utf-8")
    spec = (ROOT / "QuantumScribe-Linux.spec").read_text(encoding="utf-8")
    release = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    assert 'pip install --require-hashes -r requirements-build-linux.lock' in build_script
    assert 'pip install "pyinstaller>=6.18,<7"' not in build_script
    assert "'PIL._tkinter_finder'" in spec
    assert "'gi.repository.AyatanaAppIndicator3'" in spec
    assert "'hf_xet'" in spec
    assert "strip --strip-unneeded" in build_script
    assert "libpython*.so" in build_script
    assert "libx265-*" in build_script
    assert "upx" not in build_script.lower()
    assert "tray-icon.png" in spec
    assert "install_linux_shortcut.sh" in release


def test_one_command_linux_installer_is_safe_and_documented():
    installer = (ROOT / "install_linux_latest.sh").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "releases/latest" in installer
    assert "SHA256SUMS.txt" in installer
    assert "sha256sum" in installer
    assert 'filter="data"' in installer
    assert "install_linux_shortcut.sh" in installer
    assert "quantumscribe-install.XXXXXX" in installer
    assert "QS_SKIP_SYSTEM_DEPENDENCIES" in installer
    assert "QS_NO_START" in installer
    assert "QS_VERIFY_ONLY" in installer
    assert "curl -fsSL https://raw.githubusercontent.com/" in readme
    assert "install_linux_latest.sh | bash" in readme


def test_core_explicitly_excludes_heavy_optional_runtimes():
    spec = (ROOT / "QuantumScribe.spec").read_text(encoding="utf-8")

    assert "collect_dynamic_libs" not in spec
    assert "'torch'" in spec
    assert "'silero_vad'" in spec
    assert "'nvidia'" in spec
    assert "hiddenimports = ['onnxruntime'" not in spec
    assert "'onnxruntime'" in spec
    assert "'scipy'" not in spec
    assert "'noisereduce'" not in spec


def test_release_build_separates_core_and_optional_components():
    release = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")

    assert r".\build.ps1 -Installer" in release
    assert "build_optional_components.ps1" in release
    assert "QuantumScribe-CUDA-" in release
    assert "QuantumScribe-SileroVAD-" in release
    assert "build-linux:" in release
    assert "QuantumScribe-Core-$version-Linux-x64.tar.gz" in release
    assert "Compress-Archive" not in release
    assert '"QuantumScribe-Core-$version-Windows-x64.zip",' not in release
    assert "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02" in release
    assert "actions/download-artifact@d3f86a106a0bac45b974a628896c90dbdf5c8093" in release
    assert "needs: [build-linux, build-windows]" in release
    assert "permissions:\n      contents: write" in release
    assert 'gh release create "$tag" --repo "${{ github.repository }}"' in release
    assert 'gh release edit "$tag" --repo "${{ github.repository }}"' in release
    assert 'gh release edit "$tag" --repo "${{ github.repository }}" --draft=false --latest' in release


def test_build_scripts_enforce_core_inventory():
    windows = (ROOT / "build.ps1").read_text(encoding="utf-8")
    linux = (ROOT / "build_linux.sh").read_text(encoding="utf-8")

    assert "requirements-build.lock" in windows
    assert "--require-hashes" in windows
    assert "inventory_bundle.py" in windows
    assert "--max-bytes 262144000" in windows
    assert "requirements-build-linux.lock" in linux
    assert "--require-hashes" in linux
    assert "inventory_bundle.py" in linux


def test_backup_feature_is_not_shipped():
    assert not (ROOT / "localwhisper" / "backup.py").exists()
    settings = (ROOT / "localwhisper" / "settings_ui.py").read_text(encoding="utf-8")
    assert "Backup e Restauração" not in settings


def test_installer_has_fixed_safe_location_and_no_recursive_root_delete():
    installer = (ROOT / "installer" / "QuantumScribe.nsi").read_text(encoding="utf-8")

    assert "MUI_PAGE_DIRECTORY" not in installer
    assert 'InstallDir "$LOCALAPPDATA\\Programs\\${APP_NAME}"' in installer
    assert 'RMDir /r "$INSTDIR"' not in installer
    assert ".quantumscribe-install" in installer


def test_settings_save_does_not_depend_on_lazy_volume_widget():
    settings = (ROOT / "localwhisper" / "settings_ui.py").read_text(encoding="utf-8")

    assert "self.sound_volume_var = tk.DoubleVar" in settings
    assert "sound_volume=float(self.sound_volume_var.get())" in settings
    assert "sound_volume=float(self.volume_slider.get())" not in settings


def test_about_page_exposes_safe_application_updater():
    settings = (ROOT / "localwhisper" / "settings_ui.py").read_text(encoding="utf-8")
    updater = (ROOT / "localwhisper" / "updater.py").read_text(encoding="utf-8")

    assert '"Verificar atualização"' in settings
    assert "SHA256SUMS.txt" in updater
    assert "draft" in updater and "prerelease" in updater
    assert "Get-Process" in updater and "Start-Sleep" in updater
    assert "QuantumScribe-Setup-" in updater
    assert "QuantumScribe-Core-" in updater
    assert 'filter="data"' in updater


def test_nsis_build_uses_utf8_input():
    build_script = (ROOT / "build.ps1").read_text(encoding="utf-8")

    assert '"/INPUTCHARSET" "UTF8"' in build_script
