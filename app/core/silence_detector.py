
from typing import List
from pydub import AudioSegment, silence
from tqdm import tqdm

from .config import SilenceDetectionConfig
from .dto import TimeRange


def detect_silence_ranges(audio_path: str, config: SilenceDetectionConfig) -> List[TimeRange]:
    """Detect long silence ranges in an audio file and return them as TimeRange objects."""
    print("Loading audio file...")
    audio = AudioSegment.from_wav(audio_path)

    duration_seconds = len(audio) / 1000.0
    print(f"Audio duration: {duration_seconds:.1f}s")

    # Compute threshold relative to the overall audio loudness
    silence_thresh = audio.dBFS - config.silence_thresh_offset_db

    print(f"Analyzing audio (threshold: {silence_thresh:.1f} dBFS)...")

    # Process in chunks to show progress
    chunk_duration_ms = 60000  # 60 seconds per chunk
    total_chunks = (len(audio) + chunk_duration_ms - 1) // chunk_duration_ms

    all_silent_ranges = []

    with tqdm(total=total_chunks, desc="Detecting silences", unit="chunk", ncols=80) as pbar:
        for i in range(0, len(audio), chunk_duration_ms):
            chunk = audio[i:i + chunk_duration_ms]
            chunk_offset = i

            # Detect silence in this chunk
            silent_ranges_ms = silence.detect_silence(
                chunk,
                min_silence_len=config.min_silence_len_ms,
                silence_thresh=silence_thresh,
            )

            # Adjust ranges to absolute positions
            for start, end in silent_ranges_ms:
                all_silent_ranges.append((start + chunk_offset, end + chunk_offset))

            pbar.update(1)

    # Merge overlapping ranges from adjacent chunks
    merged_ranges = _merge_overlapping_ranges(all_silent_ranges, config.min_silence_len_ms)

    return [
        TimeRange(start=start / 1000.0, end=end / 1000.0)
        for start, end in merged_ranges
    ]


def _merge_overlapping_ranges(ranges: List[tuple], min_gap_ms: int) -> List[tuple]:
    """Merge overlapping or adjacent silence ranges."""
    if not ranges:
        return []

    # Sort by start time
    sorted_ranges = sorted(ranges, key=lambda x: x[0])
    merged = [sorted_ranges[0]]

    for current_start, current_end in sorted_ranges[1:]:
        last_start, last_end = merged[-1]

        # If ranges overlap or are very close, merge them
        if current_start <= last_end + min_gap_ms:
            merged[-1] = (last_start, max(last_end, current_end))
        else:
            merged.append((current_start, current_end))

    return merged
