"""Refresh the Field Notes list in README.md from the blog's RSS feed."""

from __future__ import annotations

import re
import urllib.request
import xml.etree.ElementTree as ElementTree
from pathlib import Path

FEED = "https://blog.mumojack.dev/rss.xml"
README = Path(__file__).resolve().parent.parent / "README.md"
START, END = "<!-- BLOG-POSTS:START -->", "<!-- BLOG-POSTS:END -->"
POSTS = 3


def main() -> None:
    # The feed refuses urllib's default User-Agent.
    request = urllib.request.Request(FEED, headers={"User-Agent": "profile-readme-updater"})
    with urllib.request.urlopen(request, timeout=30) as response:
        feed = ElementTree.fromstring(response.read())
    lines = []
    for item in list(feed.iter("item"))[:POSTS]:
        title = " ".join((item.findtext("title") or "").split()).replace(" :", ":")
        link = (item.findtext("link") or "").replace("mumojack.hashnode.dev", "blog.mumojack.dev")
        lines.append(f"- [{title}]({link})")
    if not lines:
        raise SystemExit("the feed has no posts; leaving the README alone")
    block = "\n".join([START, *lines, END])
    text = README.read_text(encoding="utf-8")
    pattern = re.escape(START) + ".*?" + re.escape(END)
    README.write_text(re.sub(pattern, lambda _: block, text, flags=re.S), encoding="utf-8")


if __name__ == "__main__":
    main()
