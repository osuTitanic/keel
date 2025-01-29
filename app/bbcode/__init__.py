
# Modified version of:
# https://github.com/dcwatson/bbcode/blob/master/bbcode.py
# Copyright (c) 2011, Dan Watson

from .formatter import parser as formatter
from .objects import TagOptions
from .parser import Parser

import urllib.parse
import re

def url_hotfix(input_text: str) -> str:
    """Fix the formatting of various URLs"""
    pattern = r'\[url=(?P<url>.*?)\](?P<name>.*?)\[/url\]'
    matches = re.finditer(pattern, input_text)

    for match in matches:
        url = match.group('url')
        unquoted_url = urllib.parse.unquote(url)

        input_text = input_text.replace(
            url,
            urllib.parse.quote(unquoted_url, safe=':/')
        )

    return input_text

def render_html(input_text, **context):
    """
    A module-level convenience method that creates a default bbcode parser,
    and renders the input string as HTML.
    """
    input_text = url_hotfix(input_text)
    return formatter.format(input_text, **context)
