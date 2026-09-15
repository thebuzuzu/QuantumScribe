from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from localwhisper.config import AppConfig
from localwhisper.speech_cleaner import clean_transcription
from localwhisper.transcriber import LocalTranscriber


class _FakeWhisperModel:
    def __init__(self, text: str, *, start: float = 0.0, end: float = 1.0) -> None:
        self.text = text
        self.start = start
        self.end = end
        self.last_options: dict = {}

    def transcribe(self, _audio, **options):
        self.last_options = options
        return iter([
            SimpleNamespace(text=self.text, start=self.start, end=self.end)
        ]), SimpleNamespace()


class LiteralCleanerTests(unittest.TestCase):
    def test_literal_mode_preserves_words_repetitions_case_and_punctuation(self) -> None:
        spoken = (
            "Por favor, eu quero que você audite o meu, o meu QuantumScribe, "
            "identifique por que que algumas palavras ele, ele tá modificando."
        )

        result = clean_transcription(
            spoken,
            remove_stutter=True,
            remove_filler_words=True,
            literal_mode=True,
        )

        self.assertEqual(result, spoken)

    def test_non_literal_mode_can_still_remove_repetition_when_requested(self) -> None:
        result = clean_transcription(
            "eu eu quero testar",
            remove_stutter=True,
            literal_mode=False,
        )

        self.assertEqual(result, "Eu quero testar")

    def test_literal_mode_still_discards_known_whisper_hallucination(self) -> None:
        self.assertIsNone(
            clean_transcription("Obrigado por assistir", literal_mode=True)
        )


class LiteralWhisperOptionsTests(unittest.TestCase):
    def test_literal_mode_disables_prompt_and_previous_text_conditioning(self) -> None:
        config = AppConfig(
            literal_mode=True,
            continuous_learning=True,
            initial_prompt="Este prompt não deve enviesar a transcrição literal.",
        )
        transcriber = LocalTranscriber(config, lambda _status: None)
        model = _FakeWhisperModel("eu eu falei exatamente isso")
        transcriber._model = model

        with tempfile.TemporaryDirectory() as tmp:
            audio_path = Path(tmp) / "audio.wav"
            audio_path.touch()
            result = transcriber.transcribe(audio_path, duration=1.0)

        self.assertEqual(result, "eu eu falei exatamente isso.")
        self.assertIsNone(model.last_options["initial_prompt"])
        self.assertFalse(model.last_options["condition_on_previous_text"])
        self.assertEqual(model.last_options["language"], "pt")
        self.assertEqual(model.last_options["task"], "transcribe")

    def test_translation_is_not_forced_into_literal_transcription_mode(self) -> None:
        config = AppConfig(literal_mode=True)
        transcriber = LocalTranscriber(config, lambda _status: None)

        self.assertFalse(transcriber._literal_mode_enabled(translate=True))

    def test_incomplete_vad_runtime_does_not_block_standard_transcription(self) -> None:
        config = AppConfig(literal_mode=True)
        transcriber = LocalTranscriber(config, lambda _status: None)
        model = _FakeWhisperModel("a transcrição continua funcionando")
        transcriber._model = model

        with patch("localwhisper.transcriber._vad_runtime_available", return_value=False):
            with tempfile.TemporaryDirectory() as tmp:
                audio_path = Path(tmp) / "audio.wav"
                audio_path.touch()
                result = transcriber.transcribe(audio_path, duration=1.0)

        self.assertEqual(result, "a transcrição continua funcionando.")
        self.assertFalse(model.last_options["vad_filter"])
        self.assertNotIn("vad_parameters", model.last_options)


if __name__ == "__main__":
    unittest.main()
