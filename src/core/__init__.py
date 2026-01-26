# Core module - platform-agnostic logic
# Implementation: see ../docs/ for specification

from .processor import process
from .contracts import (
    CoreMessageEvent, DetectedTime, TimezoneSignals, ResolvedTimeContext,
    ConvertedTime, DisplayBlock, CoreConfig, UserProfile, ChannelContext
)

__all__ = [
    'process',
    'CoreMessageEvent', 'DetectedTime', 'TimezoneSignals', 'ResolvedTimeContext',
    'ConvertedTime', 'DisplayBlock', 'CoreConfig', 'UserProfile', 'ChannelContext'
]
