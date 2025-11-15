
from typing import List
from pydub import AudioSegment, silence

from .config import SilenceDetectionConfig
from .dto import TimeRange


def detect_silence_ranges(audio_path: str, config: SilenceDetectionConfig) -> List[TimeRange]:
    """Detect long silence ranges in an audio file and return them as TimeRange objects."""
    audio = AudioSegment.from_wav(audio_path)

    # Compute threshold relative to the overall audio loudness
    silence_thresh = audio.dBFS - config.silence_thresh_offset_db

    silent_ranges_ms = silence.detect_silence(
        audio,
        min_silence_len=config.min_silence_len_ms,
        silence_thresh=silence_thresh,
    )

    return [
        TimeRange(start=start / 1000.0, end=end / 1000.0)
        for start, end in silent_ranges_ms
    ]
