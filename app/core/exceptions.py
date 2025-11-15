"""
Custom exceptions for the video lesson splitter.
"""


class VideoProcessingError(Exception):
    """Base exception for all video processing errors."""
    pass


class FFmpegNotFoundError(VideoProcessingError):
    """Raised when FFmpeg is not installed or not found in PATH."""
    
    def __init__(self, message: str = "FFmpeg not found. Please install FFmpeg: sudo apt install ffmpeg"):
        self.message = message
        super().__init__(self.message)


class FFprobeNotFoundError(VideoProcessingError):
    """Raised when FFprobe is not installed or not found in PATH."""
    
    def __init__(self, message: str = "FFprobe not found. Please install FFmpeg: sudo apt install ffmpeg"):
        self.message = message
        super().__init__(self.message)


class AudioExtractionError(VideoProcessingError):
    """Raised when audio extraction from video fails."""
    
    def __init__(self, video_path: str, reason: str = "Unknown error"):
        self.video_path = video_path
        self.reason = reason
        self.message = f"Failed to extract audio from '{video_path}': {reason}"
        super().__init__(self.message)


class SilenceDetectionError(VideoProcessingError):
    """Raised when silence detection fails."""
    
    def __init__(self, audio_path: str, reason: str = "Unknown error"):
        self.audio_path = audio_path
        self.reason = reason
        self.message = f"Failed to detect silence in '{audio_path}': {reason}"
        super().__init__(self.message)


class VideoCuttingError(VideoProcessingError):
    """Raised when video cutting/splitting fails."""
    
    def __init__(self, video_path: str, reason: str = "Unknown error"):
        self.video_path = video_path
        self.reason = reason
        self.message = f"Failed to cut video '{video_path}': {reason}"
        super().__init__(self.message)


class InvalidVideoFileError(VideoProcessingError):
    """Raised when the video file is invalid or not found."""
    
    def __init__(self, video_path: str, reason: str = "File not found or invalid format"):
        self.video_path = video_path
        self.reason = reason
        self.message = f"Invalid video file '{video_path}': {reason}"
        super().__init__(self.message)


class ConfigurationError(VideoProcessingError):
    """Raised when there's an error in configuration."""
    
    def __init__(self, message: str):
        self.message = f"Configuration error: {message}"
        super().__init__(self.message)


class NoLessonsFoundError(VideoProcessingError):
    """Raised when no valid lessons are found in the video."""
    
    def __init__(self, video_path: str, reason: str = "No silence ranges detected or all segments too short"):
        self.video_path = video_path
        self.reason = reason
        self.message = f"No lessons found in '{video_path}': {reason}"
        super().__init__(self.message)

