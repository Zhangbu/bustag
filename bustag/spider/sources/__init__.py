"""
Source adapter registry.
"""
from __future__ import annotations

import importlib

from bustag.spider.sources.base import SourceAdapter
from bustag.spider.sources.bus import BusSourceAdapter
from bustag.util import APP_CONFIG, logger


def _build_sources() -> dict[str, SourceAdapter]:
    sources: dict[str, SourceAdapter] = {'bus': BusSourceAdapter()}
    try:
        missav_mod = importlib.import_module('bustag.spider.sources.missav')
        sources['missav'] = missav_mod.MissAVSourceAdapter()
    except Exception as exc:
        logger.warning('MissAV source disabled: %s', exc)
    return sources


_SOURCES: dict[str, SourceAdapter] = _build_sources()


def get_source(name: str | None = None) -> SourceAdapter:
    source_name = name or APP_CONFIG.get('download.source', 'bus')
    try:
        return _SOURCES[source_name]
    except KeyError as exc:
        supported = ', '.join(sorted(_SOURCES))
        raise ValueError(f'Unsupported source: {source_name}. Supported: {supported}') from exc


def list_sources() -> list[str]:
    return sorted(_SOURCES)
