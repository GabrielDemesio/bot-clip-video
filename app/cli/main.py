
import os

from app.core.config import SilenceDetectionConfig, LessonSplitConfig
from app.services.module_processor import ModuleProcessor
from app.cli.menu import choose_from_list

VIDEOS_DIR = "videos_input"
OUTPUT_BASE_DIR = "lessons_output"


def ensure_directories() -> None:
    os.makedirs(VIDEOS_DIR, exist_ok=True)
    os.makedirs(OUTPUT_BASE_DIR, exist_ok=True)


def main() -> None:
    print("\n==== Video Lesson Splitter ====")
    ensure_directories()

    processor = ModuleProcessor(
        videos_dir=VIDEOS_DIR,
        output_base_dir=OUTPUT_BASE_DIR,
        silence_config=SilenceDetectionConfig(
            min_silence_len_ms=10_000,
            silence_thresh_offset_db=16.0,
        ),
        lesson_config=LessonSplitConfig(
            min_lesson_duration_sec=60,
            padding_before_sec=0.5,
            padding_after_sec=0.5,
        ),
    )

    videos = processor.list_videos()
    if not videos:
        print(
            f"No videos found in '{VIDEOS_DIR}'."
            "\nPut your raw module videos in this folder and run again."
        )
        return

    chosen = choose_from_list(videos)
    if not chosen:
        print("Exiting...")
        return

    print(f"\nSelected video: {chosen}\n")
    processor.process_video(chosen)


if __name__ == "__main__":
    main()
