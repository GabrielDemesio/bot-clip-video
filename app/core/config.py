
from dataclasses import dataclass

@dataclass
class SilenceDetectionConfig:
    """
    Configuration options for silence detection.
    min_silence_len_ms: minimum continuous silence (in milliseconds) that will be
                        considered a "cut point" between lessons.
    silence_thresh_offset_db: value subtracted from the audio average dBFS to define
                              the silence threshold (more negative = more strict).
    """
    min_silence_len_ms: int = 10_000
    silence_thresh_offset_db: float = 16.0


@dataclass
class LessonSplitConfig:
    """
    Configuration options for lesson splitting and output generation.
    min_lesson_duration_sec: minimum duration (in seconds) for a segment to be
                             considered a valid lesson.
    padding_before_sec: extra seconds added before each lesson start.
    padding_after_sec: extra seconds added after each lesson end.
    """
    min_lesson_duration_sec: int = 60
    padding_before_sec: float = 0.5
    padding_after_sec: float = 0.5
