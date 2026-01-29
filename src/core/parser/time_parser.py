"""
Time parser - regex-based time detection.
Specification: TIME_PARSING_RULES.md
"""
import re
import logging
from typing import List
from ..contracts import DetectedTime

logger = logging.getLogger(__name__)


# Compiled regex patterns (immutable, allowed by Invariant #7)
TIME_24H_REGEX = re.compile(r'\b([01]?\d|2[0-3]):([0-5]\d)\b')

# TIME_12H_AMPM: hour (1-12), optional minute, am/pm
TIME_12H_AMPM_REGEX = re.compile(
    r'\b(1[0-2]|0?[1-9])(?::([0-5]\d))?\s*(am|pm|AM|PM|a\.m\.|p\.m\.)\b',
    re.UNICODE
)

# TIME_BARE_HOUR: trigger word + hour (1-12)
# English trigger words only (Latin script)
TRIGGER_WORDS = r'(?:at|by|around|about|until|till)'
TIME_BARE_HOUR_REGEX = re.compile(
    rf'(?i)\b({TRIGGER_WORDS})\s+([1-9]|1[0-2])\b',
    re.UNICODE
)


def overlaps(match: re.Match, existing_results: List[DetectedTime]) -> bool:
    """
    Check if match overlaps with any existing result.
    Positions are character indices in the original string.
    """
    for r in existing_results:
        # Overlap if intervals intersect (half-open intervals [start, end))
        if not (match.end() <= r.position_start or match.start() >= r.position_end):
            return True
    return False


def parse_times(text: str, max_results: int = 3) -> List[DetectedTime]:
    """
    Parse time mentions from text.
    
    Args:
        text: Message text to parse
        max_results: Maximum times to return (default: 3, from CoreConfig)
    
    Returns:
        List of DetectedTime, sorted by position, capped to max_results
    
    Priority order (changed to ensure 12H with AM/PM wins over bare 24H):
        1. TIME_12H_AMPM - most specific (includes AM/PM marker)
        2. TIME_24H - less specific (no AM/PM)
        3. TIME_BARE_HOUR - least specific (ambiguous)
    
    Rationale: "10:30am" must be recognized as 12-hour format per TIME_PARSING_RULES.md §1.2.
    If TIME_24H were first, it would match "10:30" and the AM/PM would be lost.
    
    Input length limit: 4096 characters (aligned with Telegram message limit).
    Protects against ReDoS and ensures bounded complexity.
    """
    # Truncate input to prevent ReDoS on very long messages
    # 4096 is Telegram's message limit, also a reasonable bound for complexity
    MAX_TEXT_LENGTH = 4096
    if len(text) > MAX_TEXT_LENGTH:
        logger.debug(f"Input text truncated from {len(text)} to {MAX_TEXT_LENGTH} chars")
        text = text[:MAX_TEXT_LENGTH]
    
    results = []
    
    # Priority 1: TIME_12H_AMPM (most specific - includes AM/PM marker)
    # This MUST be checked first so "10:30am" is recognized as 12-hour format
    # Error Handling: Skip invalid matches, continue with others (TIME_PARSING_RULES.md §5)
    for match in TIME_12H_AMPM_REGEX.finditer(text):
        try:
            hour = int(match.group(1))
            minute = int(match.group(2)) if match.group(2) else None
            am_pm_group = match.group(3)
            if not am_pm_group:
                continue  # Skip if AM/PM group is missing
            am_pm_raw = am_pm_group.upper().replace('.', '')  # Normalize "a.m." → "AM"
            # Regex guarantees format is "AM" or "PM" after normalization
            am_pm = am_pm_raw if am_pm_raw in ("AM", "PM") else None
            
            results.append(DetectedTime(
                raw_text=match.group(),
                hour=hour,
                minute=minute,
                am_pm=am_pm,
                position_start=match.start(),
                position_end=match.end(),
                ambiguous=False
            ))
        except (ValueError, IndexError) as e:
            # Skip invalid match, continue with others (per TIME_PARSING_RULES.md §5)
            logger.debug(f"Skipped invalid TIME_12H_AMPM match '{match.group()}': {e}")
            continue
    
    # Priority 2: TIME_24H (skip if overlaps with existing 12H matches)
    # Error Handling: Skip invalid matches, continue with others
    for match in TIME_24H_REGEX.finditer(text):
        if not overlaps(match, results):
            try:
                hour = int(match.group(1))
                minute = int(match.group(2))
                results.append(DetectedTime(
                    raw_text=match.group(),
                    hour=hour,
                    minute=minute,
                    am_pm=None,
                    position_start=match.start(),
                    position_end=match.end(),
                    ambiguous=False
                ))
            except (ValueError, IndexError) as e:
                # Skip invalid match, continue with others (per TIME_PARSING_RULES.md §5)
                logger.debug(f"Skipped invalid TIME_24H match '{match.group()}': {e}")
                continue
    
    # Priority 3: TIME_BARE_HOUR (skip if overlaps)
    # Error Handling: Skip invalid matches, continue with others
    for match in TIME_BARE_HOUR_REGEX.finditer(text):
        if not overlaps(match, results):
            try:
                hour = int(match.group(2))  # group(1) is trigger word
                results.append(DetectedTime(
                    raw_text=match.group(),
                    hour=hour,
                    minute=None,
                    am_pm=None,
                    position_start=match.start(),
                    position_end=match.end(),
                    ambiguous=True  # Always ambiguous
                ))
            except (ValueError, IndexError) as e:
                # Skip invalid match, continue with others (per TIME_PARSING_RULES.md §5)
                logger.debug(f"Skipped invalid TIME_BARE_HOUR match '{match.group()}': {e}")
                continue
    
    # Sort by position, cap to max_results
    return sorted(results, key=lambda x: x.position_start)[:max_results]
