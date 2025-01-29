
import re

# Adapted from http://daringfireball.net/2010/07/improved_regex_for_matching_urls
# Changed to only support one level of parentheses, since it was failing catastrophically on some URLs.
# See http://www.regular-expressions.info/catastrophic.html
_url_re = re.compile(
    r"(?im)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)"
    r'(?:[^\s()<>]+|\([^\s()<>]+\))+(?:\([^\s()<>]+\)|[^\s`!()\[\]{};:\'".,<>?]))'
)

# For the URL tag, try to be smart about when to append a missing http://. If the given link looks like a domain,
# add a http:// in front of it, otherwise leave it alone (since it may be a relative path, a filename, etc).
_domain_re = re.compile(
    r"(?im)(?:www\d{0,3}[.]|[a-z0-9.\-]+[.](?:com|net|org|edu|biz|gov|mil|info|io|name|me|tv|us|uk|mobi))"
)
