import os
import tempfile
from pathlib import Path


class SpeechToTextService:
    """Local Whisper-class STT when faster-whisper is installed."""

    def __init__(self):
        self._model = None
        self.model_size = os.getenv(
            "WHISPER_MODEL_SIZE",
            "base"
        )

    def is_available(self) -> bool:
        try:
            import faster_whisper  # noqa: F401
            return True
        except ImportError:
            return False

    def _load_model(self):
        if self._model is not None:
            return self._model

        from faster_whisper import WhisperModel

        device = os.getenv("WHISPER_DEVICE", "cpu")
        compute_type = os.getenv(
            "WHISPER_COMPUTE_TYPE",
            "int8"
        )

        self._model = WhisperModel(
            self.model_size,
            device=device,
            compute_type=compute_type
        )

        return self._model

    def transcribe_bytes(
        self,
        audio_bytes: bytes,
        filename: str = "audio.webm"
    ) -> str:

        if not self.is_available():
            raise RuntimeError(
                "Local speech-to-text is not installed. "
                "Install faster-whisper or type your answer."
            )

        suffix = Path(filename).suffix or ".webm"

        with tempfile.NamedTemporaryFile(
            suffix=suffix,
            delete=False
        ) as temp_file:
            temp_file.write(audio_bytes)
            temp_path = temp_file.name

        try:
            model = self._load_model()
            segments, _info = model.transcribe(
                temp_path,
                vad_filter=True
            )
            parts = [
                segment.text.strip()
                for segment in segments
                if segment.text.strip()
            ]
            text = " ".join(parts).strip()
            if not text:
                raise ValueError(
                    "Could not pick up speech. Try again or type."
                )
            return text
        finally:
            Path(temp_path).unlink(missing_ok=True)
