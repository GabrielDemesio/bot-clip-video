"""
Tests for validators module.
"""

import os
import tempfile
import pytest

from app.core.validators import (
    validate_video_file,
    validate_output_directory,
    get_video_files_in_directory,
    SUPPORTED_VIDEO_FORMATS
)
from app.core.exceptions import InvalidVideoFileError


class TestValidateVideoFile:
    """Tests for validate_video_file function."""
    
    def test_valid_video_file(self):
        """Test validation of a valid video file."""
        # Create a temporary video file
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
            f.write(b'fake video content')
            temp_path = f.name
        
        try:
            assert validate_video_file(temp_path) is True
        finally:
            os.unlink(temp_path)
    
    def test_nonexistent_file(self):
        """Test validation of non-existent file."""
        with pytest.raises(InvalidVideoFileError) as exc_info:
            validate_video_file('/path/to/nonexistent/video.mp4')
        
        assert "File not found" in str(exc_info.value)
    
    def test_unsupported_format(self):
        """Test validation of unsupported file format."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b'not a video')
            temp_path = f.name
        
        try:
            with pytest.raises(InvalidVideoFileError) as exc_info:
                validate_video_file(temp_path)
            
            assert "Unsupported format" in str(exc_info.value)
        finally:
            os.unlink(temp_path)
    
    def test_empty_file(self):
        """Test validation of empty file."""
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
            temp_path = f.name
        
        try:
            with pytest.raises(InvalidVideoFileError) as exc_info:
                validate_video_file(temp_path)
            
            assert "File is empty" in str(exc_info.value)
        finally:
            os.unlink(temp_path)


class TestValidateOutputDirectory:
    """Tests for validate_output_directory function."""
    
    def test_create_directory(self):
        """Test creating output directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = os.path.join(temp_dir, 'output')
            
            assert not os.path.exists(output_dir)
            assert validate_output_directory(output_dir, create_if_missing=True) is True
            assert os.path.exists(output_dir)
    
    def test_existing_directory(self):
        """Test validation of existing directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            assert validate_output_directory(temp_dir) is True


class TestGetVideoFilesInDirectory:
    """Tests for get_video_files_in_directory function."""
    
    def test_get_video_files(self):
        """Test getting video files from directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create some video files
            video_files = ['video1.mp4', 'video2.avi', 'video3.mkv']
            for filename in video_files:
                path = os.path.join(temp_dir, filename)
                with open(path, 'w') as f:
                    f.write('fake content')
            
            # Create a non-video file
            with open(os.path.join(temp_dir, 'readme.txt'), 'w') as f:
                f.write('not a video')
            
            # Get video files
            found_videos = get_video_files_in_directory(temp_dir)
            
            assert len(found_videos) == 3
            for video_path in found_videos:
                assert os.path.basename(video_path) in video_files
    
    def test_empty_directory(self):
        """Test getting video files from empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            found_videos = get_video_files_in_directory(temp_dir)
            assert found_videos == []
    
    def test_nonexistent_directory(self):
        """Test getting video files from non-existent directory."""
        found_videos = get_video_files_in_directory('/path/to/nonexistent')
        assert found_videos == []

