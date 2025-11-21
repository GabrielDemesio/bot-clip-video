
import os
from typing import List

from app.core.config import SilenceDetectionConfig, LessonSplitConfig
from app.core.dto import LessonSegment
from app.core.video_splitter import split_video_into_lessons
from app.core.utils import format_time
from app.core.validators import validate_video_file, get_video_files_in_directory
from app.core.exceptions import InvalidVideoFileError
from app.core.logger import get_logger

logger = get_logger(__name__)


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
        """List all video files in the videos directory."""
        video_paths = get_video_files_in_directory(self.videos_dir)
        return [os.path.basename(path) for path in video_paths]

    def process_video(self, video_filename: str) -> List[LessonSegment]:
        """
        Process a video file and split it into lessons.

        Args:
            video_filename: Name of the video file in videos_dir

        Returns:
            List of LessonSegment objects

        Raises:
            InvalidVideoFileError: If video file is invalid
        """
        video_path = os.path.join(self.videos_dir, video_filename)
        validate_video_file(video_path)

        video_basename, _ = os.path.splitext(os.path.basename(video_path))
        output_dir = os.path.join(self.output_base_dir, video_basename)
        os.makedirs(output_dir, exist_ok=True)

        print(f"Output directory: {output_dir}")
        logger.info(f"Processing video: {video_path}")
        logger.info(f"Output directory: {output_dir}")

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
            logger.info(f"Generated {len(lessons)} lessons")
        else:
            print("No lessons generated.")
            logger.warning("No lessons were generated")

        return lessons
