
import os
import re
import subprocess
from typing import Callable, List, Optional

from moviepy import VideoFileClip
from tqdm import tqdm

from .config import SilenceDetectionConfig, LessonSplitConfig
from .dto import TimeRange, LessonSegment
from .silence_detector import detect_silence_ranges
from .utils import format_time
from .exceptions import (
    FFmpegNotFoundError,
    FFprobeNotFoundError,
    AudioExtractionError,
    VideoCuttingError,
    NoLessonsFoundError
)
from .logger import get_logger

logger = get_logger(__name__)


Logger = Callable[[str], None]


def _extract_audio_ffmpeg(video_path: str, audio_path: str, video_duration: float, logger: Optional[Logger] = None) -> None:
    """Extract audio from video using FFmpeg directly with progress bar."""
    if logger:
        logger("Extracting audio with FFmpeg...")

    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-vn",
        "-ar", "8000",
        "-ac", "1",
        "-f", "wav",
        "-y",
        "-progress", "pipe:2",
        audio_path
    ]

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )

        with tqdm(total=100, desc="Extracting audio", unit="%", ncols=80) as pbar:
            last_progress = 0

            for line in process.stderr:
                match = re.search(r'out_time_ms=(\d+)', line)
                if match:
                    time_us = int(match.group(1))
                    time_s = time_us / 1_000_000
                    progress = min(100, int((time_s / video_duration) * 100))

                    delta = progress - last_progress
                    if delta > 0:
                        pbar.update(delta)
                        last_progress = progress

        return_code = process.wait()

        if return_code != 0:
            stderr_output = process.stderr.read() if process.stderr else ""
            raise AudioExtractionError(video_path, f"FFmpeg exit code {return_code}: {stderr_output}")

        if logger:
            logger(f"✓ Audio extracted to: {audio_path}")

    except FileNotFoundError:
        raise FFmpegNotFoundError()
    except Exception as e:
        if not isinstance(e, (FFmpegNotFoundError, AudioExtractionError)):
            raise AudioExtractionError(video_path, str(e))


def _get_video_duration_ffmpeg(video_path: str) -> float:
    """Get video duration using FFmpeg (faster than loading with moviepy)."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path
    ]

    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        duration = float(result.stdout.decode().strip())
        return duration
    except FileNotFoundError:
        raise FFprobeNotFoundError()
    except (subprocess.CalledProcessError, ValueError):
        try:
            video = VideoFileClip(video_path)
            duration = video.duration
            video.close()
            return duration
        except Exception as e:
            raise AudioExtractionError(video_path, f"Failed to get video duration: {e}")


def _cut_video_ffmpeg(
    video_path: str,
    output_path: str,
    start_time: float,
    end_time: float,
    logger: Optional[Logger] = None
) -> None:
    """Cut video segment using FFmpeg (much faster than moviepy with codec copy)."""
    duration = end_time - start_time

    cmd = [
        "ffmpeg",
        "-ss", str(start_time),
        "-i", video_path,
        "-t", str(duration),
        "-c", "copy",
        "-avoid_negative_ts", "make_zero",
        "-y",
        output_path
    ]

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        if logger:
            logger(f"  ✓ Saved")
    except FileNotFoundError:
        raise FFmpegNotFoundError()
    except subprocess.CalledProcessError as e:
        raise VideoCuttingError(video_path, f"FFmpeg error: {e.stderr.decode()}")


def _build_non_silent_ranges(
    silent_ranges: List[TimeRange],
    video_duration: float,
) -> List[TimeRange]:
    """Compute non-silent ranges (lessons) as the complement of silence intervals."""
    if not silent_ranges:
        return [TimeRange(0.0, video_duration)]

    non_silent: List[TimeRange] = []

    first_silence = silent_ranges[0]
    if first_silence.start > 0:
        non_silent.append(TimeRange(0.0, first_silence.start))

    for prev, nxt in zip(silent_ranges, silent_ranges[1:]):
        non_silent.append(TimeRange(prev.end, nxt.start))

    last_silence = silent_ranges[-1]
    if last_silence.end < video_duration:
        non_silent.append(TimeRange(last_silence.end, video_duration))

    return non_silent


def split_video_into_lessons(
    video_path: str,
    output_dir: str,
    silence_config: Optional[SilenceDetectionConfig] = None,
    lesson_config: Optional[LessonSplitConfig] = None,
    logger: Optional[Logger] = print,
) -> List[LessonSegment]:
    """Split a video into lesson files based on silent intervals.

    Returns a list of LessonSegment objects describing the generated lessons.
    """
    if silence_config is None:
        silence_config = SilenceDetectionConfig()

    if lesson_config is None:
        lesson_config = LessonSplitConfig()

    if logger is None:
        logger = lambda *_args, **_kwargs: None

    os.makedirs(output_dir, exist_ok=True)

    video_name = os.path.basename(video_path)
    logger(f"=== Processing video: {video_name} ===")

    temp_audio_path = os.path.join(output_dir, "_temp_audio.wav")

    logger("Getting video info...")
    video_duration = _get_video_duration_ffmpeg(video_path)
    logger(f"Video duration: {format_time(video_duration)}")

    _extract_audio_ffmpeg(video_path, temp_audio_path, video_duration, logger)

    logger("Detecting silence ranges...")
    silent_ranges = detect_silence_ranges(temp_audio_path, silence_config)

    if not silent_ranges:
        logger("No long silences found. The whole video will be considered as one lesson.")

    else:
        logger("Silences detected:")
        for r in silent_ranges:
            logger(f"  {format_time(r.start)} -> {format_time(r.end)}")

    non_silent_ranges = _build_non_silent_ranges(silent_ranges, video_duration)

    logger("\nRaw non-silent ranges (before filters):")
    for r in non_silent_ranges:
        logger(f"  {format_time(r.start)} -> {format_time(r.end)} ({r.duration():.1f}s)")

    filtered_ranges: List[TimeRange] = [
        r for r in non_silent_ranges
        if r.duration() >= lesson_config.min_lesson_duration_sec
    ]

    if not filtered_ranges:
        logger("No segments were long enough to be considered lessons.")
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
        raise NoLessonsFoundError(video_path, "All segments too short after filtering")

    logger("\nFinal lesson ranges (after filters):")
    for idx, r in enumerate(filtered_ranges, start=1):
        logger(f"  Lesson {idx:02d}: {format_time(r.start)} -> {format_time(r.end)} ({r.duration():.1f}s)")

    lessons: List[LessonSegment] = []
    logger("\nGenerating lesson files...")

    with tqdm(total=len(filtered_ranges), desc="Cutting videos", unit="lesson", ncols=80) as pbar:
        for idx, r in enumerate(filtered_ranges, start=1):
            clip_start = max(0.0, r.start - lesson_config.padding_before_sec)
            clip_end = min(video_duration, r.end + lesson_config.padding_after_sec)

            output_filename = f"lesson_{idx:02d}.mp4"
            output_path = os.path.join(output_dir, output_filename)

            pbar.set_description(f"Cutting lesson {idx:02d}/{len(filtered_ranges)}")

            _cut_video_ffmpeg(video_path, output_path, clip_start, clip_end, logger)

            lessons.append(LessonSegment(start=clip_start, end=clip_end, index=idx))
            pbar.update(1)

    if os.path.exists(temp_audio_path):
        os.remove(temp_audio_path)

    logger("\nDone processing this video.\n")
    return lessons
