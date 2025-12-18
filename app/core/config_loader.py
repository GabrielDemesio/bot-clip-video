"""
Configuration loader for the video lesson splitter.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from .config import SilenceDetectionConfig, LessonSplitConfig
from .exceptions import ConfigurationError


DEFAULT_CONFIG_PATH = "config.yaml"


def load_yaml_config(config_path: str = DEFAULT_CONFIG_PATH) -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to YAML config file
    
    Returns:
        Dictionary with configuration
    
    Raises:
        ConfigurationError: If config file is invalid or not found
    """
    if not os.path.exists(config_path):
        raise ConfigurationError(f"Config file not found: {config_path}")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if config is None:
            raise ConfigurationError(f"Config file is empty: {config_path}")
        
        return config
    
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Invalid YAML in config file: {e}")
    except Exception as e:
        raise ConfigurationError(f"Failed to load config file: {e}")


def get_silence_detection_config(config: Optional[Dict[str, Any]] = None) -> SilenceDetectionConfig:
    """
    Get SilenceDetectionConfig from loaded config or use defaults.
    
    Args:
        config: Loaded configuration dictionary
    
    Returns:
        SilenceDetectionConfig instance
    """
    if config is None:
        return SilenceDetectionConfig()
    
    silence_config = config.get('silence_detection', {})
    
    return SilenceDetectionConfig(
        min_silence_len_ms=silence_config.get('min_silence_len_ms', 10000),
        silence_thresh_offset_db=silence_config.get('silence_thresh_offset_db', 30)
    )


def get_lesson_split_config(config: Optional[Dict[str, Any]] = None) -> LessonSplitConfig:
    """
    Get LessonSplitConfig from loaded config or use defaults.
    
    Args:
        config: Loaded configuration dictionary
    
    Returns:
        LessonSplitConfig instance
    """
    if config is None:
        return LessonSplitConfig()
    
    lesson_config = config.get('lesson_split', {})
    
    return LessonSplitConfig(
        min_lesson_duration_sec=lesson_config.get('min_lesson_duration_sec', 60),
        padding_before_sec=lesson_config.get('padding_before_sec', 2),
        padding_after_sec=lesson_config.get('padding_after_sec', 2)
    )


def get_paths_config(config: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    """
    Get paths configuration.
    
    Args:
        config: Loaded configuration dictionary
    
    Returns:
        Dictionary with paths
    """
    if config is None:
        return {
            'videos_input': 'videos_input',
            'lessons_output': 'lessons_output'
        }
    
    paths_config = config.get('paths', {})
    
    return {
        'videos_input': paths_config.get('videos_input', 'videos_input'),
        'lessons_output': paths_config.get('lessons_output', 'lessons_output')
    }


def get_logging_config(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Get logging configuration.
    
    Args:
        config: Loaded configuration dictionary
    
    Returns:
        Dictionary with logging settings
    """
    if config is None:
        return {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'save_to_file': False,
            'log_file': 'video_splitter.log'
        }
    
    logging_config = config.get('logging', {})
    
    return {
        'level': logging_config.get('level', 'INFO'),
        'format': logging_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
        'save_to_file': logging_config.get('save_to_file', False),
        'log_file': logging_config.get('log_file', 'video_splitter.log')
    }


def get_audio_extraction_config(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Get audio extraction configuration.
    
    Args:
        config: Loaded configuration dictionary
    
    Returns:
        Dictionary with audio extraction settings
    """
    if config is None:
        return {
            'sample_rate': 8000,
            'channels': 1
        }
    
    audio_config = config.get('audio_extraction', {})
    
    return {
        'sample_rate': audio_config.get('sample_rate', 8000),
        'channels': audio_config.get('channels', 1)
    }


def get_video_processing_config(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Get video processing configuration.

    Args:
        config: Loaded configuration dictionary

    Returns:
        Dictionary with video processing settings
    """
    if config is None:
        return {
            'codec': 'copy',
            'audio_codec': 'copy'
        }

    video_config = config.get('video_processing', {})

    return {
        'codec': video_config.get('codec', 'copy'),
        'audio_codec': video_config.get('audio_codec', 'copy')
    }


def get_s3_sync_config(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Get S3 sync configuration.

    Args:
        config: Loaded configuration dictionary

    Returns:
        Dictionary with S3 sync settings
    """
    if config is None:
        return {
            'enabled': False,
            'bucket_name': '',
            's3_prefix': '',
            'aws_profile': '',
            'auto_sync': False
        }

    s3_config = config.get('s3_sync', {})

    return {
        'enabled': s3_config.get('enabled', False),
        'bucket_name': s3_config.get('bucket_name', ''),
        's3_prefix': s3_config.get('s3_prefix', ''),
        'aws_profile': s3_config.get('aws_profile', ''),
        'auto_sync': s3_config.get('auto_sync', False)
    }
