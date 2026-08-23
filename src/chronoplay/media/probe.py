from __future__ import annotations

import json
import subprocess
from fractions import Fraction
from pathlib import Path

from chronoplay.media.metadata import MediaMetadata


class MediaProbeError(RuntimeError):
    """Raised when media metadata cannot be extracted."""


class FFprobeMediaProbe:
    def __init__(self, executable: str = "ffprobe") -> None:
        self.executable = executable

    def probe(self, path: str | Path) -> MediaMetadata:
        media_path = Path(path)

        if not media_path.is_file():
            raise MediaProbeError(f"media file does not exist: {media_path}")

        command = [
            self.executable,
            "-v",
            "error",
            "-show_format",
            "-show_streams",
            "-of",
            "json",
            str(media_path),
        ]

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            raise MediaProbeError(
                f"failed to probe media file: {media_path}"
            ) from exc

        try:
            data = json.loads(result.stdout)
            return self._build_metadata(data)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise MediaProbeError(
                f"invalid media metadata: {media_path}"
            ) from exc

    @staticmethod
    def _build_metadata(data: dict) -> MediaMetadata:
        streams = data.get("streams", [])
        format_data = data.get("format", {})

        video_stream = next(
            (stream for stream in streams if stream.get("codec_type") == "video"),
            None,
        )
        audio_stream = next(
            (stream for stream in streams if stream.get("codec_type") == "audio"),
            None,
        )

        if not format_data.get("format_name"):
            raise ValueError("missing container format")

        duration = float(format_data["duration"])

        frame_rate = None
        if video_stream and video_stream.get("avg_frame_rate") not in {
            None,
            "0/0",
        }:
            frame_rate = Fraction(video_stream["avg_frame_rate"])

        return MediaMetadata(
            duration=duration,
            container=format_data["format_name"],
            video_codec=(
                video_stream.get("codec_name") if video_stream else None
            ),
            audio_codec=(
                audio_stream.get("codec_name") if audio_stream else None
            ),
            width=video_stream.get("width") if video_stream else None,
            height=video_stream.get("height") if video_stream else None,
            frame_rate=frame_rate,
            audio_channels=(
                audio_stream.get("channels") if audio_stream else None
            ),
        )
