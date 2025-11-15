
import os
from typing import List

from app.core.config import SilenceDetectionConfig, LessonSplitConfig
from app.core.dto import LessonSegment
from app.core.video_splitter import split_video_into_lessons
from app.core.utils import format_time


class ModuleProcessor:
    """
    High-level service to process a single module video into multiple lesson clips.
    """

    def __init__(
        self,
        videos_dir: str,
        output_base_dir: str,
        silence_config: SilenceDetectionConfig | None = None,
        lesson_config: LessonSplitConfig | None = None,
    ) -> None:
        self.videos_dir = videos_dir
        self.output_base_dir = output_base_dir
        self.silence_config = silence_config or SilenceDetectionConfig()
        self.lesson_config = lesson_config or LessonSplitConfig()

    def list_videos(self) -> List[str]:
        if not os.path.isdir(self.videos_dir):
            return []
        files = [
            f
            for f in os.listdir(self.videos_dir)
            if f.lower().endswith((".mp4", ".mkv", ".mov", ".avi"))
        ]
        return sorted(files)

    def process_video(self, video_filename: str) -> List[LessonSegment]:
        video_path = os.path.join(self.videos_dir, video_filename)
        if not os.path.isfile(video_path):
            raise FileNotFoundError(f"Video not found: {video_path}")

        video_basename, _ = os.path.splitext(os.path.basename(video_path))
        output_dir = os.path.join(self.output_base_dir, video_basename)
        os.makedirs(output_dir, exist_ok=True)

        print(f"Output directory: {output_dir}")
        lessons = split_video_into_lessons(
            video_path=video_path,
            output_dir=output_dir,
            silence_config=self.silence_config,
            lesson_config=self.lesson_config,
            logger=print,
        )

        if lessons:
            print("\nSummary of generated lessons:")
            for lesson in lessons:
                print(
                    f"  Lesson {lesson.index:02d}: "
                    f"{format_time(lesson.start)} -> {format_time(lesson.end)}"
                    f" ({lesson.duration():.1f}s)"
                )
        else:
            print("No lessons generated.")

        return lessons
