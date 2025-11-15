
import os
import sys

from app.core.config_loader import (
    load_yaml_config,
    get_silence_detection_config,
    get_lesson_split_config,
    get_paths_config,
    get_logging_config
)
from app.core.logger import setup_logger
from app.core.validators import validate_ffmpeg_installed, validate_ffprobe_installed
from app.core.exceptions import VideoProcessingError, ConfigurationError
from app.services.module_processor import ModuleProcessor
from app.cli.menu import choose_from_list


def ensure_directories(videos_dir: str, output_dir: str) -> None:
    """Ensure required directories exist."""
    os.makedirs(videos_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)


def main() -> None:
    """Main entry point for the video lesson splitter."""
    print("\n==== Video Lesson Splitter ====\n")

    try:
        # Load configuration
        try:
            config = load_yaml_config()
            print("✓ Configuration loaded from config.yaml")
        except ConfigurationError as e:
            print(f"⚠ Warning: {e}")
            print("Using default configuration...\n")
            config = None

        # Setup logging
        logging_config = get_logging_config(config)
        logger = setup_logger(
            __name__,
            level=logging_config['level'],
            log_format=logging_config['format'],
            save_to_file=logging_config['save_to_file'],
            log_file=logging_config['log_file']
        )

        # Validate FFmpeg installation
        try:
            validate_ffmpeg_installed()
            validate_ffprobe_installed()
            print("✓ FFmpeg and FFprobe are installed\n")
        except VideoProcessingError as e:
            print(f"✗ Error: {e}")
            print("\nPlease install FFmpeg:")
            print("  Ubuntu/Debian: sudo apt install ffmpeg")
            print("  macOS: brew install ffmpeg")
            print("  Windows: Download from https://ffmpeg.org/download.html")
            sys.exit(1)

        # Get paths from config
        paths = get_paths_config(config)
        videos_dir = paths['videos_input']
        output_base_dir = paths['lessons_output']

        # Ensure directories exist
        ensure_directories(videos_dir, output_base_dir)

        # Get processing configs
        silence_config = get_silence_detection_config(config)
        lesson_config = get_lesson_split_config(config)

        # Create processor
        processor = ModuleProcessor(
            videos_dir=videos_dir,
            output_base_dir=output_base_dir,
            silence_config=silence_config,
            lesson_config=lesson_config,
        )

        # List and choose video
        videos = processor.list_videos()
        if not videos:
            print(f"No videos found in '{videos_dir}'.")
            print("\nPut your raw module videos in this folder and run again.")
            return

        chosen = choose_from_list(videos)
        if not chosen:
            print("Exiting...")
            return

        print(f"\nSelected video: {chosen}\n")

        # Process video
        processor.process_video(chosen)

        print("\n✓ Processing completed successfully!")

    except VideoProcessingError as e:
        print(f"\n✗ Error: {e}")
        logger.error(f"Video processing failed: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        logger.exception("Unexpected error occurred")
        sys.exit(1)


if __name__ == "__main__":
    main()
