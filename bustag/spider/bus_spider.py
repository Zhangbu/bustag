"""
Backward-compatible wrappers for the default bus source adapter.
"""
from bustag.spider.sources import get_source

adapter = get_source('bus')
router = adapter.router
process_item = adapter.process_item
process_page = adapter.process_page
verify_fanhao = adapter.verify_fanhao
verify_page_path = adapter.verify_page_path
MAXPAGE = adapter.max_page


def get_url_by_fanhao(fanhao):
    return adapter.get_item_url(fanhao)
