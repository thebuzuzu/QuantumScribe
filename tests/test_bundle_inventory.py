import json
import os
from pathlib import Path

import pytest

from scripts.inventory_bundle import build_inventory, main


def test_inventory_is_deterministic_and_contains_sha256(tmp_path: Path):
    artifact = tmp_path / "artifact"
    artifact.mkdir()
    (artifact / "b.txt").write_text("b", encoding="utf-8")
    (artifact / "a.txt").write_text("a", encoding="utf-8")

    first = build_inventory(artifact, max_bytes=1024)
    second = build_inventory(artifact, max_bytes=1024)

    assert first == second
    assert [entry["path"] for entry in first["files"]] == ["a.txt", "b.txt"]
    assert all(len(entry["sha256"]) == 64 for entry in first["files"])
    assert first["policy"]["passed"] is True


def test_inventory_rejects_forbidden_content_names_and_size(tmp_path: Path):
    artifact = tmp_path / "artifact"
    artifact.mkdir()
    (artifact / "onnxruntime.dll").write_bytes(b"optional")
    (artifact / "model.onnx").write_bytes(b"model")

    report = tmp_path / "inventory.json"
    assert main([str(artifact), "--output", str(report), "--max-bytes", "1"]) == 1

    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["policy"]["passed"] is False
    assert {item["path"] for item in payload["forbidden_matches"]} == {
        "model.onnx",
        "onnxruntime.dll",
    }


def test_inventory_excludes_its_output_when_inside_artifact(tmp_path: Path):
    artifact = tmp_path / "artifact"
    artifact.mkdir()
    (artifact / "app.exe").write_bytes(b"app")
    report = artifact / "inventory.json"

    assert main([str(artifact), "--output", str(report)]) == 0
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert [entry["path"] for entry in payload["files"]] == ["app.exe"]


def test_inventory_counts_symlink_metadata_without_double_counting_target(tmp_path: Path):
    artifact = tmp_path / "artifact"
    artifact.mkdir()
    target = artifact / "payload.bin"
    target.write_bytes(b"payload")
    alias = artifact / "alias.bin"
    try:
        os.symlink(target.name, alias)
    except (OSError, NotImplementedError):
        pytest.skip("symlink não disponível neste ambiente")

    payload = build_inventory(artifact, max_bytes=1024)

    assert payload["total_bytes"] == len(b"payload")
    link = next(entry for entry in payload["files"] if entry["path"] == "alias.bin")
    assert link["bytes"] == 0
    assert link["type"] == "symlink"
    assert link["target"] == "payload.bin"
    assert payload["policy"]["passed"] is True
