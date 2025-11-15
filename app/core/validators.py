"""
Validation utilities for video files and configurations.
"""

import os
import shutil
from pathlib import Path
from typing import List

from .exceptions import InvalidVideoFileError, FFmpegNotFoundError, FFprobeNotFoundError


# Supported video formats
SUPPORTED_VIDEO_FORMATS = {
    '.mp4', '.avi', '.mkv', '.mov', '.flv', 
    '.wmv', '.webm', '.m4v', '.mpg', '.mpeg'
}


def validate_video_file(video_path: str) -> bool:
    """
    Validate if the file exists and is a supported video format.
    
    Args:
        video_path: Path to the video file
    
    Returns:
        True if valid
    
    Raises:
        InvalidVideoFileError: If file doesn't exist or has invalid format
    """
    # Check if file exists
    if not os.path.exists(video_path):
        raise InvalidVideoFileError(video_path, "File not found")
    
    # Check if it's a file (not a directory)
    if not os.path.isfile(video_path):
        raise InvalidVideoFileError(video_path, "Path is not a file")
    
    # Check file extension
    file_extension = Path(video_path).suffix.lower()
    if file_extension not in SUPPORTED_VIDEO_FORMATS:
        supported = ', '.join(sorted(SUPPORTED_VIDEO_FORMATS))
        raise InvalidVideoFileError(
            video_path, 
            f"Unsupported format '{file_extension}'. Supported: {supported}"
        )
    
    # Check if file is readable
    if not os.access(video_path, os.R_OK):
        raise InvalidVideoFileError(video_path, "File is not readable")
    
    # Check if file is not empty
    if os.path.getsize(video_path) == 0:
        raise InvalidVideoFileError(video_path, "File is empty")
    
    return True


def validate_ffmpeg_installed() -> bool:
    """
    Check if FFmpeg is installed and available in PATH.
    
    Returns:
        True if FFmpeg is installed
    
    Raises:
        FFmpegNotFoundError: If FFmpeg is not found
    """
    if shutil.which("ffmpeg") is None:
        raise FFmpegNotFoundError()
    return True


def validate_ffprobe_installed() -> bool:
    """
    Check if FFprobe is installed and available in PATH.
    
    Returns:
        True if FFprobe is installed
    
    Raises:
        FFprobeNotFoundError: If FFprobe is not found
    """
    if shutil.which("ffprobe") is None:
        raise FFprobeNotFoundError()
    return True


def validate_output_directory(output_dir: str, create_if_missing: bool = True) -> bool:
    """
    Validate output directory exists and is writable.
    
    Args:
        output_dir: Path to output directory
        create_if_missing: Create directory if it doesn't exist
    
    Returns:
        True if valid
    
    Raises:
        InvalidVideoFileError: If directory is not writable
    """
    # Create directory if it doesn't exist
    if not os.path.exists(output_dir):
        if create_if_missing:
            os.makedirs(output_dir, exist_ok=True)
        else:
            raise InvalidVideoFileError(output_dir, "Output directory does not exist")
    
    # Check if it's a directory
    if not os.path.isdir(output_dir):
        raise InvalidVideoFileError(output_dir, "Path is not a directory")
    
    # Check if directory is writable
    if not os.access(output_dir, os.W_OK):
        raise InvalidVideoFileError(output_dir, "Output directory is not writable")
    
    return True


def get_video_files_in_directory(directory: str) -> List[str]:
    """
    Get all video files in a directory.
    
    Args:
        directory: Path to directory
    
    Returns:
        List of video file paths
    """
    if not os.path.exists(directory):
        return []
    
    video_files = []
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            file_extension = Path(file_path).suffix.lower()
            if file_extension in SUPPORTED_VIDEO_FORMATS:
                video_files.append(file_path)
    
    return sorted(video_files)

