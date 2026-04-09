"""
Source adapter registry.
"""
from __future__ import annotations

from bustag.spider.sources.base import SourceAdapter
from bustag.spider.sources.bus import BusSourceAdapter
from bustag.spider.sources.missav import MissAVSourceAdapter
from bustag.util import APP_CONFIG

_SOURCES: dict[str, SourceAdapter] = {
    'bus': BusSourceAdapter(),
    'missav': MissAVSourceAdapter(),
}


def get_source(name: str | None = None) -> SourceAdapter:
    source_name = name or APP_CONFIG.get('download.source', 'bus')
    try:
        return _SOURCES[source_name]
    except KeyError as exc:
        supported = ', '.join(sorted(_SOURCES))
        raise ValueError(f'Unsupported source: {source_name}. Supported: {supported}') from exc


def list_sources() -> list[str]:
    return sorted(_SOURCES)
