"""
DisplayBlock to Telegram message formatter.
Specification: TELEGRAM_ADAPTER.md §4, ADAPTER_CONTRACTS.md §6
"""
import json
import logging
from pathlib import Path
from typing import Dict, List
from core.contracts import DisplayBlock

logger = logging.getLogger(__name__)


def load_cities_index(cities_path: str) -> Dict[str, str]:
    """
    Load cities.json and build city→timezone index.
    
    Args:
        cities_path: Path to cities.json
    
    Returns:
        Dictionary mapping lowercase city/alias -> timezone ID
    """
    path = Path(cities_path)
    if not path.exists():
        return {}
    
    with open(path, 'r', encoding='utf-8') as f:
        cities_data = json.load(f)
    
    if not isinstance(cities_data, list):
        return {}
    
    index = {}
    
    def normalize_city_key(text: str) -> str:
        """Normalize city name by removing dots for abbreviation matching.
        
        This allows "St. Petersburg" and "St Petersburg" to match the same entry.
        """
        return text.lower().replace('.', '')
    
    for entry in cities_data:
        timezone = entry.get("timezone")
        if not timezone:
            continue
        
        # Add primary city name (both exact and normalized versions)
        city = entry.get("city", "")
        if city:
            city_lower = city.lower()
            city_normalized = normalize_city_key(city)
            # Store exact match (preserves original capitalization info)
            index[city_lower] = timezone
            # Store normalized match (for abbreviations like "St." -> "st")
            if city_normalized != city_lower:
                index[city_normalized] = timezone
        
        # Add aliases (both exact and normalized versions)
        for alias in entry.get("aliases", []):
            if alias:
                alias_lower = alias.lower()
                alias_normalized = normalize_city_key(alias)
                # Store exact match
                index[alias_lower] = timezone
                # Store normalized match
                if alias_normalized != alias_lower:
                    index[alias_normalized] = timezone
    
    return index


def load_cities_data(cities_path: str) -> list:
    """
    Load cities.json as list of dicts.
    
    Args:
        cities_path: Path to cities.json
    
    Returns:
        List of city entries
    """
    path = Path(cities_path)
    if not path.exists():
        return []
    
    with open(path, 'r', encoding='utf-8') as f:
        cities_data = json.load(f)
    
    if not isinstance(cities_data, list):
        return []
    
    return cities_data


def get_cities_for_timezone(timezone_id: str, cities_data: List[dict]) -> List[str]:
    """
    Get list of city names for a given timezone.
    
    Args:
        timezone_id: IANA timezone ID or offset string (±HH:MM)
        cities_data: Loaded cities.json data
    
    Returns:
        List of city names (sorted alphabetically)
        Empty list if timezone_id is an offset string (cities.json only contains IANA IDs)
    """
    import re
    
    # Offset strings don't have cities in cities.json
    # cities.json only maps cities to IANA timezone IDs
    if re.match(r'^[+-]\d{2}:\d{2}$', timezone_id):
        return []
    
    cities = []
    for entry in cities_data:
        if entry.get("timezone") == timezone_id:
            city_name = entry.get("city")
            if city_name:
                cities.append(city_name)
            # Also add aliases
            for alias in entry.get("aliases", []):
                if alias:
                    cities.append(alias)
    
    return sorted(cities)


def format_display_block_with_cities(
    display_block: DisplayBlock,
    cities_data: List[dict]
) -> str:
    """
    Format DisplayBlock to Telegram message text with proper city names.
    
    Args:
        display_block: DisplayBlock from core
        cities_data: Loaded cities.json data (list of dicts)
    
    Returns:
        Formatted text string
    """
    lines = []
    
    logger.debug(f"Formatting DisplayBlock with {len(display_block.entries)} entries")
    for entry in display_block.entries:
        timezone_id = entry["timezone"]
        local_time = entry["local_time"]
        
        # Get cities for this timezone
        cities = get_cities_for_timezone(timezone_id, cities_data)
        
        # Format line
        if cities:
            cities_str = ", ".join(cities)
            line = f"{local_time} {timezone_id} ({cities_str})"
        else:
            line = f"{local_time} {timezone_id}"
        
        logger.debug(f"Formatted entry: {line}")
        lines.append(line)
    
    formatted_text = "\n".join(lines)
    logger.info(f"Formatted message ({len(lines)} lines):\n{formatted_text}")
    return formatted_text
