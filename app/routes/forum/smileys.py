
import re

SMILEY_REPLACEMENTS = (
    (":roll:", "[smiley]269[/smiley]"),
    (":shock:", "[smiley]75[/smiley]"),
    (":arrow:", "[smiley]247[/smiley]"),
    (":idea:", "[smiley]261[/smiley]"),
    (":lol:", "[smiley]262[/smiley]"),
    (":oops:", "[smiley]268[/smiley]"),
    (":cry:", "[smiley]55[/smiley]"),
    (":!:", "[smiley]260[/smiley]"),
    (":?:", "[smiley]266[/smiley]"),
    ("8-)", "[smiley]248[/smiley]"),
    (">:(", "[smiley]51[/smiley]"),
    (":)", "[smiley]50[/smiley]"),
    (":D", "[smiley]242[/smiley]"),
    (";)", "[smiley]59[/smiley]"),
    (":o", "[smiley]57[/smiley]"),
    (":(", "[smiley]56[/smiley]"),
    (":?", "[smiley]60[/smiley]"),
    (":x", "[smiley]51[/smiley]"),
    (":P", "[smiley]58[/smiley]"),
    (":|", "[smiley]52[/smiley]"),
)

RAW_TAGS = {
    "c",
    "code",
    "email",
    "google",
    "img",
    "smiley",
    "url",
    "video",
    "youtube",
}

URL_RE = re.compile(
    r"""(?im)\b("""
    r"""(?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,}/)"""
    r"""(?:[^\s()<>]+|\([^\s()<>]+\))+"""
    r"""(?:\([^\s()<>]+\)|[^\s`!()\[\]{};:'".,<>?])"""
    r""")"""
)

def normalize_smileys(text: str) -> str:
    result: list[str] = []
    active_raw_tag: str | None = None
    position = 0

    while position < len(text):
        tag_start = text.find("[", position)
        if tag_start == -1:
            # No more tags found -> replace smileys in the rest of the text
            result.append(
                replace_smileys_in_text(
                    text[position:],
                    skip=active_raw_tag is not None,
                )
            )
            break

        result.append(
            replace_smileys_in_text(
                text[position:tag_start],
                skip=active_raw_tag is not None,
            )
        )

        tag_end = text.find("]", tag_start)
        if tag_end == -1:
            # No closing bracket found -> replace smileys in the rest of the text
            result.append(
                replace_smileys_in_text(
                    text[tag_start:],
                    skip=active_raw_tag is not None,
                )
            )
            break

        # We found a tag, we will add it to the result and check if it is a raw tag
        # If not, we will continue replacing smileys in the text after it

        tag = text[tag_start : tag_end + 1]
        tag_name, is_closing = parse_tag(tag)

        result.append(tag)
        position = tag_end + 1

        if active_raw_tag is None:
            if not is_closing and tag_name in RAW_TAGS:
                active_raw_tag = tag_name
        elif is_closing and tag_name == active_raw_tag:
            active_raw_tag = None

    return "".join(result)

def replace_smileys_in_text(text: str, *, skip: bool = False) -> str:
    if skip:
        return text

    # Replace smileys while leaving URLs unchanged
    result: list[str] = []
    position = 0

    for match in URL_RE.finditer(text):
        result.append(replace_smileys(text[position : match.start()]))
        result.append(match.group(0))
        position = match.end()

    result.append(replace_smileys(text[position:]))
    return "".join(result)

def replace_smileys(text: str) -> str:
    for smiley, replacement in SMILEY_REPLACEMENTS:
        text = text.replace(smiley, replacement)
    return text

def parse_tag(tag: str) -> tuple[str, bool]:
    # Return a bbcode tag normalized name & whether it is closing
    body = tag[1:-1].strip()
    is_closing = body.startswith("/")

    if is_closing:
        body = body[1:].lstrip()

    name = re.split(r"[=\s]", body, maxsplit=1)[0]
    return name.lower(), is_closing
