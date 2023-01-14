from requests_cache import CacheMixin
from requests_html import HTMLSession


class CachedHTMLSession(CacheMixin, HTMLSession):
    """Session with features from both CachedSession and HTMLSession"""
