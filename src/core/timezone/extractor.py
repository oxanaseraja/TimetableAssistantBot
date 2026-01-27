"""
Timezone extraction from message text.
Specification: TIMEZONE_EXTRACTION_RULES.md
"""
import re
import zoneinfo
from typing import Optional, Mapping, List


def tokenize(text: str) -> List[str]:
    """
    Split text into word tokens.
    Uses word boundaries, preserves Unicode letters, hyphens, and dots.
    Lowercasing is done during comparison, not here.
    
    Pattern: \b[\w.-]+\b captures:
    - Unicode letters (\w): A-Z, a-z, 0-9, _, and Unicode letters
    - Hyphens (-): for compound names like "Saint-Petersburg"
    - Dots (.): for abbreviations like "St.", "Dr.", "Mt."
    """
    return re.findall(r'\b[\w.-]+\b', text, re.UNICODE)


def normalize_offset(raw: str) -> Optional[str]:
    """
    Normalize timezone offset to ±HH:MM format.
    
    Input formats: +3, +03, +0300, +03:00, UTC+3, GMT-5
    Output format: +03:00, -05:00
    
    Returns:
        Normalized offset string (±HH:MM) or None if format is invalid or out of range.
        Invalid offsets MUST NOT be converted into "+00:00" to preserve signal integrity.
    
    Validation rules:
        - Hours: [0, 14] (UTC offsets typically ±12, but allow up to ±14 for edge cases)
        - Minutes: [0, 59]
        - Offsets outside range → return None (ignored)
    
    Rationale:
        Returning None on invalid format ensures:
        - Signal integrity (no false explicit hints)
        - No hallucinated defaults (system doesn't invent UTC)
        - Fail transparent (errors are visible to resolver)
    """
    try:
        # Remove UTC/GMT prefix
        raw = re.sub(r'^(UTC|GMT)', '', raw, flags=re.IGNORECASE)
        
        # Check for empty string after prefix removal
        if not raw:
            return None
        
        # Extract sign
        sign = '+' if raw[0] != '-' else '-'
        raw = raw.lstrip('+-')
        
        # Check for empty string after sign removal
        if not raw:
            return None
        
        # Parse hours and minutes
        if ':' in raw:
            parts = raw.split(':')
            hours, minutes = int(parts[0]), int(parts[1])
        elif len(raw) >= 3:
            hours = int(raw[:2])
            minutes = int(raw[2:4]) if len(raw) >= 4 else 0
        else:
            hours = int(raw)
            minutes = 0
        
        # Validate range: hours [0, 14], minutes [0, 59]
        # Specification: TIMEZONE_EXTRACTION_RULES.md - Offset Range Validation
        if not (0 <= hours <= 14) or not (0 <= minutes <= 59):
            return None  # Out of range - ignore invalid offset
        
        return f"{sign}{hours:02d}:{minutes:02d}"
    except (ValueError, IndexError):
        # Invalid offset format - return None to indicate no explicit hint found
        # This preserves signal integrity: invalid offsets are ignored, not converted to UTC
        return None


def extract_timezone_hint(
    text: str,
    time_position: int,
    city_index: Mapping[str, str],
    window: int = 30
) -> Optional[str]:
    """
    Extract timezone hint from context around time mention.
    
    Args:
        text: Full message text
        time_position: Character position of time mention
        city_index: Pre-built city→timezone lookup (passed from adapter)
        window: Characters to look before/after (default 30)
    
    Returns:
        IANA timezone ID, normalized offset, or None
    
    Note: city_index is passed explicitly to maintain core purity (Invariant #7).
    """
    start = max(0, time_position - window)
    end = min(len(text), time_position + window)
    context = text[start:end]
    
    # Priority 1: UTC/GMT offset
    # Specification: TIMEZONE_EXTRACTION_RULES.md §4 - Ambiguity Handling
    # If multiple matches, use closest to time_position
    # If distances are equal → select first by text order (left-to-right) for determinism
    TZ_OFFSET_REGEX = re.compile(r'(UTC|GMT)?[+-]\d{1,2}(:\d{2})?', re.IGNORECASE)
    offset_matches = list(TZ_OFFSET_REGEX.finditer(context))
    if offset_matches:
        # Find closest match to time_position
        # Distance calculation: abs((start + m.start()) - time_position)
        # m.start() is position in context, start + m.start() is absolute position in original text
        # 
        # Edge case - Equal distances:
        # When multiple matches have equal distance to time_position, we use tuple key
        # (distance, text_position) to ensure deterministic selection:
        # - First sort by distance (abs difference)
        # - If distances are equal, sort by text_position (m.start())
        # - min() with tuple key guarantees first match by text order (left-to-right)
        # This ensures same input → same output (deterministic behavior)
        closest_match = min(
            offset_matches,
            key=lambda m: (abs((start + m.start()) - time_position), m.start())
        )
        return normalize_offset(closest_match.group())
    
    # Priority 2: IANA timezone ID
    # If multiple matches, use closest to time_position
    TZ_IANA_REGEX = re.compile(r'\b[A-Za-z_]+/[A-Za-z_]+\b')
    iana_matches = list(TZ_IANA_REGEX.finditer(context))
    if iana_matches:
        # Find closest valid IANA timezone
        valid_matches = []
        for match in iana_matches:
            tz_id = match.group()
            try:
                if tz_id in zoneinfo.available_timezones():
                    valid_matches.append((match, tz_id))
            except Exception:
                pass
        
        if valid_matches:
            # Find closest match to time_position
            # Specification: TIMEZONE_EXTRACTION_RULES.md §4 - Ambiguity Handling
            # x[0].start() is position in context, start + x[0].start() is absolute position in original text
            # 
            # Edge case - Equal distances:
            # When multiple IANA timezones have equal distance to time_position, we use tuple key
            # (distance, text_position) to ensure deterministic selection (first by text order, left-to-right)
            # This ensures same input → same output (deterministic behavior)
            closest_match, tz_id = min(
                valid_matches,
                key=lambda x: (abs((start + x[0].start()) - time_position), x[0].start())
            )
            return tz_id
    
    # Priority 3: City lookup (uses passed index)
    # If multiple matches, use closest to time_position
    city_matches = []
    
    # Strategy: Check both single words and multi-word phrases
    # Pattern supports:
    # - Single words: "Amsterdam", "Tokyo"
    # - Words with hyphens: "Saint-Petersburg", "Buenos-Aires"
    # - Words with dots: "St.", "Dr.", "Mt." (abbreviations)
    # - Multi-word phrases: "New York", "The Hague", "St. Petersburg"
    # 
    # Pattern: \b[\w.-]+\b captures words that may contain hyphens and dots
    # This matches: "Amsterdam", "Saint-Petersburg", "St.", "New", "York"
    word_pattern = re.compile(r'\b[\w.-]+\b', re.UNICODE)
    
    # Helper function to normalize city name for lookup
    # Removes dots from abbreviations (e.g., "St." -> "st") for flexible matching
    def normalize_for_lookup(text: str) -> str:
        """Normalize text by removing dots for abbreviation matching."""
        return text.lower().replace('.', '')
    
    # First, try single words/tokens (for cities like "Amsterdam", "Tokyo", "Saint-Petersburg")
    for match in word_pattern.finditer(context):
        word = match.group()
        word_normalized = normalize_for_lookup(word)
        
        # Check exact match (with dots)
        if word.lower() in city_index:
            token_pos = match.start()
            city_matches.append((token_pos, city_index[word.lower()]))
        # Check normalized match (without dots) for abbreviations
        elif word_normalized in city_index:
            token_pos = match.start()
            city_matches.append((token_pos, city_index[word_normalized]))
    
    # Second, try multi-word phrases (for cities like "New York", "The Hague", "St. Petersburg")
    # Check all possible word sequences (2-3 words) in the context
    # This handles cities with spaces in their names
    words_list = word_pattern.findall(context)
    words_positions = [(m.start(), m.group()) for m in word_pattern.finditer(context)]
    
    # Check 2-word phrases (e.g., "New York", "Den Haag", "Saint Petersburg", "St. Petersburg")
    for i in range(len(words_list) - 1):
        phrase_2 = f"{words_list[i]} {words_list[i+1]}".lower()
        phrase_2_normalized = normalize_for_lookup(phrase_2)
        
        # Check exact match
        if phrase_2 in city_index:
            pos = words_positions[i][0]
            city_matches.append((pos, city_index[phrase_2]))
        # Check normalized match (handles "St. Petersburg" -> "st petersburg")
        elif phrase_2_normalized in city_index:
            pos = words_positions[i][0]
            city_matches.append((pos, city_index[phrase_2_normalized]))
    
    # Check 3-word phrases (e.g., "The Hague", "Saint Petersburg Russia")
    for i in range(len(words_list) - 2):
        phrase_3 = f"{words_list[i]} {words_list[i+1]} {words_list[i+2]}".lower()
        phrase_3_normalized = normalize_for_lookup(phrase_3)
        
        # Check exact match
        if phrase_3 in city_index:
            pos = words_positions[i][0]
            city_matches.append((pos, city_index[phrase_3]))
        # Check normalized match
        elif phrase_3_normalized in city_index:
            pos = words_positions[i][0]
            city_matches.append((pos, city_index[phrase_3_normalized]))
    
    if city_matches:
        # Find closest city to time_position
        # Specification: TIMEZONE_EXTRACTION_RULES.md §4 - Ambiguity Handling
        # x[0] is position in context, start + x[0] is absolute position in original text
        # 
        # Edge case - Equal distances:
        # When multiple cities have equal distance to time_position, we use tuple key
        # (distance, text_position) to ensure deterministic selection (first by text order, left-to-right)
        # This ensures same input → same output (deterministic behavior)
        closest_pos, tz_id = min(
            city_matches,
            key=lambda x: (abs((start + x[0]) - time_position), x[0])
        )
        return tz_id
    
    return None
