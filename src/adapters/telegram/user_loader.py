"""
User and channel data loader from users.json
Specification: USER_PROFILE_MODEL.md
"""
import json
import hashlib
import logging
import re
import zoneinfo
from pathlib import Path
from typing import Dict, Optional, List
from core.contracts import UserProfile, ChannelContext

logger = logging.getLogger(__name__)


def compute_active_timezones(
    channel_config: dict,
    user_configs: Dict[str, dict]
) -> List[str]:
    """
    Active timezones = unique non-null timezones of all channel members.
    
    Computed on every message. Not cached globally.
    """
    timezones = set()
    
    for member_key in channel_config.get("members", []):
        user = user_configs.get(member_key)
        if user and user.get("timezone"):
            tz = user["timezone"]
            # Validate timezone ID (USER_PROFILE_MODEL.md §9)
            # Reject offset strings explicitly - only IANA timezone IDs are allowed
            try:
                if isinstance(tz, str):
                    # Reject offset strings explicitly (USER_PROFILE_MODEL.md §9)
                    if re.match(r'^[+-]\d{2}:\d{2}$', tz):
                        logger.warning(f"Offset string '{tz}' not allowed in user profile for member {member_key}, excluding from active_timezones")
                        continue
                    # Validate IANA timezone ID
                    if tz in zoneinfo.available_timezones():
                        timezones.add(tz)
                    else:
                        logger.warning(f"Invalid timezone '{tz}' for member {member_key}, excluding from active_timezones")
                else:
                    logger.warning(f"Invalid timezone type '{type(tz).__name__}' for member {member_key} (expected string), excluding from active_timezones")
            except (TypeError, AttributeError) as e:
                logger.warning(f"Error validating timezone '{tz}' for member {member_key}: {e}, excluding from active_timezones")
            except Exception as e:
                logger.warning(f"Unexpected error validating timezone '{tz}' for member {member_key}: {e}, excluding from active_timezones")
    
    # Sorted for determinism
    return sorted(list(timezones))


def load_users(users_path: str) -> Dict[str, dict]:
    """
    Load users.json file.
    
    Args:
        users_path: Path to users.json
    
    Returns:
        Dictionary mapping platform_user_id -> user config
    """
    path = Path(users_path)
    if not path.exists():
        return {}
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, dict):
        logger.warning("users.json root is not a dict, treating as empty {}")
        return {}
    
    # Remove _comment if present
    data.pop("_comment", None)
    
    return data


def get_user_profile(
    platform_user_id: str,
    users_data: Dict[str, dict]
) -> UserProfile:
    """
    Get UserProfile for a platform user ID.
    
    Args:
        platform_user_id: Platform user ID (e.g., "telegram:123456789")
        users_data: Loaded users.json data
    
    Returns:
        UserProfile with hashed internal_user_id
    """
    # Hash platform user ID (platform_user_id already contains "telegram:" prefix, e.g., "telegram:123456789")
    # Must match format used in event_mapping.py: sha256(f"telegram:{numeric_id}")
    # Since platform_user_id is already "telegram:{numeric_id}", use it directly
    internal_user_id = hashlib.sha256(platform_user_id.encode()).hexdigest()
    
    # Lookup timezone
    user_config = users_data.get(platform_user_id, {})
    timezone = user_config.get("timezone") if user_config else None
    
    # Validate timezone ID (USER_PROFILE_MODEL.md §9)
    if timezone:
        # Reject offset strings explicitly (USER_PROFILE_MODEL.md §9)
        if re.match(r'^[+-]\d{2}:\d{2}$', timezone):
            logger.warning(f"Offset string '{timezone}' not allowed in user profile for {platform_user_id}, treating as None")
            timezone = None
        else:
            try:
                if timezone not in zoneinfo.available_timezones():
                    # Invalid timezone, treat as None
                    logger.warning(f"Invalid timezone '{timezone}' for user {platform_user_id}, treating as None")
                    timezone = None
            except Exception:
                # Error checking timezones, treat as None
                logger.warning(f"Error validating timezone '{timezone}' for user {platform_user_id}, treating as None")
                timezone = None
    
    return UserProfile(
        internal_user_id=internal_user_id,
        timezone=timezone
    )


def get_channel_context(
    platform_chat_id: str,
    users_data: Dict[str, dict]
) -> ChannelContext:
    """
    Get ChannelContext for a platform chat ID.
    
    Args:
        platform_chat_id: Platform chat ID (e.g., "-1001234567890")
        users_data: Loaded users.json data
    
    Returns:
        ChannelContext with hashed internal_channel_id and active timezones
    """
    # Hash platform chat ID (must match format used in event_mapping.py)
    internal_channel_id = hashlib.sha256(f"telegram:{platform_chat_id}".encode()).hexdigest()
    
    # Lookup channel config
    channel_key = f"channel:{platform_chat_id}"
    channel_config = users_data.get(channel_key, {})
    
    default_timezone = channel_config.get("default_timezone")
    
    # Validate default_timezone (USER_PROFILE_MODEL.md §9)
    if default_timezone:
        # Reject offset strings explicitly (USER_PROFILE_MODEL.md §9)
        if re.match(r'^[+-]\d{2}:\d{2}$', default_timezone):
            logger.warning(f"Offset string '{default_timezone}' not allowed in channel default_timezone for {platform_chat_id}, treating as None")
            default_timezone = None
        else:
            try:
                if default_timezone not in zoneinfo.available_timezones():
                    logger.warning(f"Invalid default_timezone '{default_timezone}' for channel {platform_chat_id}, treating as None")
                    default_timezone = None
            except Exception:
                logger.warning(f"Error validating default_timezone '{default_timezone}' for channel {platform_chat_id}, treating as None")
                default_timezone = None
    
    # Compute active timezones from members (validation happens inside compute_active_timezones)
    active_timezones = compute_active_timezones(channel_config, users_data)
    
    return ChannelContext(
        internal_channel_id=internal_channel_id,
        default_timezone=default_timezone,
        active_timezones=tuple(active_timezones)  # Convert to tuple for immutability
    )
