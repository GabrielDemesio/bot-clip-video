
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.core.config_loader import (
    load_yaml_config,
    get_silence_detection_config,
    get_lesson_split_config,
    get_paths_config,
    get_logging_config,
    get_s3_sync_config
)
from app.core.logger import setup_logger
from app.core.validators import validate_ffmpeg_installed, validate_ffprobe_installed
from app.core.exceptions import VideoProcessingError, ConfigurationError
from app.services.module_processor import ModuleProcessor
from app.services.s3_sync import S3Syncer, S3SyncError
from app.cli.menu import choose_from_list
from app.cli.s3_sync_cli import browse_s3_prefix


def ensure_directories(videos_dir: str, output_dir: str) -> None:
    """Ensure required directories exist."""
    os.makedirs(videos_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)


def prompt_s3_sync(output_dir: str, s3_config: dict, logger) -> None:
    """
    Prompt user to sync processed videos to S3.

    Args:
        output_dir: Directory containing processed videos
        s3_config: S3 configuration dictionary
        logger: Logger instance
    """
    if not s3_config.get('enabled', False):
        return

    print("\n" + "="*60)
    print("📤 AWS S3 Sync")
    print("="*60)
    sync_choice = input("\nDo you want to sync the processed videos to S3? (y/n): ").strip().lower()

    if sync_choice != 'y':
        print("Skipping S3 sync.")
        return

    try:
        env_bucket = os.getenv("S3_BUCKET", "")
        default_bucket = s3_config.get('bucket_name', env_bucket)
        bucket_input = input(f"\nS3 Bucket name [{default_bucket}]: ").strip()
        bucket_name = bucket_input if bucket_input else default_bucket

        default_profile = s3_config.get('aws_profile', '')
        profile_input = input(f"AWS Profile (leave empty for default) [{default_profile}]: ").strip()
        aws_profile = profile_input if profile_input else default_profile

        if not aws_profile:
            aws_profile = None

        env_prefix = os.getenv("S3_PREFIX", "")
        default_prefix = s3_config.get('s3_prefix', env_prefix)
        prefix_input = input(f"Pasta/prefixo no S3 [{default_prefix}] (digite '?' para navegar): ").strip()
        if prefix_input == "?":
            navigator = S3Syncer(bucket_name=bucket_name, s3_prefix="")
            selected = browse_s3_prefix(navigator, aws_profile=aws_profile, start_prefix="")
            if selected is None:
                print("Sync cancelled.")
                return
            s3_prefix = selected or ""
        else:
            s3_prefix = prefix_input if prefix_input else default_prefix

        # Ajuste de prefixo: se for diretório, incluir o nome da pasta de saída
        if os.path.isdir(output_dir):
            base = os.path.basename(output_dir.rstrip("/"))
            normalized = s3_prefix.strip("/")
            if not normalized.endswith(base):
                normalized = f"{normalized}/{base}" if normalized else base
            s3_prefix = normalized

        print(f"\n📋 Sync Configuration:")
        print(f"   Bucket:  {bucket_name}")
        print(f"   Prefix:  {s3_prefix}")
        print(f"   Profile: {aws_profile or 'default'}")
        print(f"   Source:  {output_dir}")

        confirm = input("\nProceed with sync? (y/n): ").strip().lower()
        if confirm != 'y':
            print("Sync cancelled.")
            return

        syncer = S3Syncer(
            bucket_name=bucket_name,
            s3_prefix=s3_prefix
        )

        success = syncer.sync_directory(
            local_dir=output_dir,
            aws_profile=aws_profile
        )

        if success:
            logger.info(f"Successfully synced {output_dir} to S3")
        else:
            logger.warning(f"S3 sync completed with errors")

    except S3SyncError as e:
        print(f"\n✗ S3 Sync Error: {e}")
        logger.error(f"S3 sync failed: {e}")
    except Exception as e:
        print(f"\n✗ Unexpected error during S3 sync: {e}")
        logger.exception("Unexpected error during S3 sync")


def main() -> None:
    """Main entry point for the video lesson splitter."""
    print("\n==== Video Lesson Splitter ====\n")

    try:
        try:
            config = load_yaml_config()
            print("✓ Configuration loaded from config.yaml")
        except ConfigurationError as e:
            print(f"⚠ Warning: {e}")
            print("Using default configuration...\n")
            config = None

        logging_config = get_logging_config(config)
        logger = setup_logger(
            __name__,
            level=logging_config['level'],
            log_format=logging_config['format'],
            save_to_file=logging_config['save_to_file'],
            log_file=logging_config['log_file']
        )

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

        paths = get_paths_config(config)
        videos_dir = paths['videos_input']
        output_base_dir = paths['lessons_output']

        ensure_directories(videos_dir, output_base_dir)

        silence_config = get_silence_detection_config(config)
        lesson_config = get_lesson_split_config(config)

        processor = ModuleProcessor(
            videos_dir=videos_dir,
            output_base_dir=output_base_dir,
            silence_config=silence_config,
            lesson_config=lesson_config,
        )

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

        lessons = processor.process_video(chosen)

        print("\n✓ Processing completed successfully!")

        video_basename = os.path.splitext(chosen)[0]
        video_output_dir = os.path.join(output_base_dir, video_basename)

        if lessons and os.path.isdir(video_output_dir):
            s3_config = get_s3_sync_config(config)
            prompt_s3_sync(video_output_dir, s3_config, logger)

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
