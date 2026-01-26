"""
Configuration loader - loads and validates configuration.yaml
Specification: ADAPTER_CONTRACTS.md §5
"""
import yaml
import os
import zoneinfo
import logging
from pathlib import Path
from typing import Dict, Any
from .contracts import CoreConfig

logger = logging.getLogger(__name__)


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to configuration.yaml
    
    Returns:
        Dictionary with configuration values
    
    Raises:
        FileNotFoundError: if config file doesn't exist
        yaml.YAMLError: if YAML is invalid
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    if config is None:
        config = {}
    
    return config


def _validate_int_config(
    value: Any,
    name: str,
    default: int,
    min_val: int,
    max_val: int
) -> int:
    """
    Validate integer configuration value with type conversion and range check.
    
    Specification: ADAPTER_CONTRACTS.md §5 - Type and Range Validation
    
    Args:
        value: Raw configuration value
        name: Configuration parameter name (for logging)
        default: Default value to use if validation fails
        min_val: Minimum allowed value
        max_val: Maximum allowed value
    
    Returns:
        Validated integer value
    """
    try:
        # Type conversion: attempt to convert string to int
        if isinstance(value, str):
            int_value = int(value)
        elif isinstance(value, int):
            int_value = value
        else:
            logger.warning(f"{name} has invalid type '{type(value).__name__}', using default {default}")
            return default
        
        # Range validation
        if not (min_val <= int_value <= max_val):
            logger.warning(f"{name}={int_value} out of range [{min_val}, {max_val}], using default {default}")
            return default
        
        return int_value
    except (ValueError, TypeError):
        logger.warning(f"Invalid {name} value '{value}', using default {default}")
        return default


def build_core_config(config_dict: Dict[str, Any]) -> CoreConfig:
    """
    Build CoreConfig from configuration dictionary with full validation.
    
    Specification: ADAPTER_CONTRACTS.md §5 - Configuration Validation Rules
    
    Args:
        config_dict: Configuration dictionary from YAML
    
    Returns:
        CoreConfig object with validated values
    """
    core_section = config_dict.get("core", {})
    output_section = config_dict.get("output", {})
    
    # Validate max_time_mentions: int, range [1, 100]
    max_time_mentions_raw = core_section.get("max_time_mentions", 3)
    max_time_mentions = _validate_int_config(max_time_mentions_raw, "max_time_mentions", 3, 1, 100)
    
    # Validate max_timezones: int, range [1, 100]
    max_timezones_raw = output_section.get("max_timezones", 5)
    max_timezones = _validate_int_config(max_timezones_raw, "max_timezones", 5, 1, 100)
    
    # Validate ordering: string, must be one of valid values
    ordering_str = output_section.get("ordering", "SOURCE_FIRST")
    if not isinstance(ordering_str, str):
        logger.warning(f"ordering has invalid type '{type(ordering_str).__name__}', using default 'SOURCE_FIRST'")
        ordering = "SOURCE_FIRST"
    elif ordering_str == "OFFSET_ASC":
        ordering = "OFFSET_ASC"
    elif ordering_str == "ALPHABETICAL":
        ordering = "ALPHABETICAL"
    elif ordering_str == "SOURCE_FIRST":
        ordering = "SOURCE_FIRST"
    else:
        logger.warning(f"Invalid ordering value '{ordering_str}', must be one of ['SOURCE_FIRST', 'OFFSET_ASC', 'ALPHABETICAL'], using default 'SOURCE_FIRST'")
        ordering = "SOURCE_FIRST"
    
    # Validate default_timezone: string or null
    default_timezone = core_section.get("default_timezone", None)
    # None means UTC in contract (CONTRACTS.md §128)
    if default_timezone is None or default_timezone == "UTC":
        default_timezone = None
    elif not isinstance(default_timezone, str):
        logger.warning(f"default_timezone has invalid type '{type(default_timezone).__name__}', treating as null (UTC)")
        default_timezone = None
    else:
        # Validate IANA timezone ID
        try:
            if default_timezone not in zoneinfo.available_timezones():
                logger.warning(f"Invalid IANA timezone ID '{default_timezone}', treating as null (UTC)")
                default_timezone = None
        except Exception as e:
            logger.warning(f"Error validating default_timezone '{default_timezone}': {e}, treating as null (UTC)")
            default_timezone = None
    
    return CoreConfig(
        max_time_mentions=max_time_mentions,
        max_timezones=max_timezones,
        ordering=ordering,
        default_timezone=default_timezone
    )


def validate_telegram_config(config_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate Telegram adapter configuration values.
    
    Specification: ADAPTER_CONTRACTS.md §5 - Configuration Validation Rules
    
    Args:
        config_dict: Configuration dictionary from YAML
    
    Returns:
        Dictionary with validated telegram config values
    """
    telegram_section = config_dict.get("telegram", {})
    validated = {}
    
    # Validate max_lines: int, range [1, 100]
    max_lines_raw = telegram_section.get("max_lines", 5)
    validated["max_lines"] = _validate_int_config(max_lines_raw, "max_lines", 5, 1, 100)
    
    # Validate retry_attempts: int, range [1, 10]
    retry_attempts_raw = telegram_section.get("retry_attempts", 3)
    validated["retry_attempts"] = _validate_int_config(retry_attempts_raw, "retry_attempts", 3, 1, 10)
    
    return validated
