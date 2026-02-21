#!/usr/bin/env python3
"""Pick AI/tech news candidates from RSS feeds.

Reads feeds from a file (one URL per line). Filters entries from last N hours and by keywords.
Outputs JSON list of candidates: [{title,url,source,published}]

Usage:
  python pick_ai_news.py --feeds /home/robo/.openclaw/workspace/feeds.md --hours 24 --limit 15
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path

import feedparser

KEYWORDS = re.compile(r"\b(ai|artificial intelligence|llm|agent|agents|copilot|gemini|openai|anthropic|deepmind|model|models|inference|training|chip|gpu|nvidia)\b", re.I)


def read_feeds(path: str) -> list[str]:
    lines = Path(path).read_text(encoding='utf-8').splitlines()
    out = []
    for ln in lines:
        s = ln.strip()
        if not s or s.startswith('#'):
            continue
        out.append(s)
    return out


def parse_dt(entry) -> dt.datetime | None:
    # feedparser may provide published_parsed or updated_parsed
    t = getattr(entry, 'published_parsed', None) or getattr(entry, 'updated_parsed', None)
    if not t:
        return None
    return dt.datetime(*t[:6], tzinfo=dt.timezone.utc)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--feeds', required=True)
    ap.add_argument('--hours', type=int, default=24)
    ap.add_argument('--limit', type=int, default=15)
    args = ap.parse_args()

    now = dt.datetime.now(dt.timezone.utc)
    cutoff = now - dt.timedelta(hours=args.hours)

    cands = []
    for url in read_feeds(args.feeds):
        d = feedparser.parse(url)
        src = (d.feed.get('title') or d.feed.get('link') or url)
        for e in d.entries or []:
            title = (getattr(e, 'title', '') or '').strip()
            link = (getattr(e, 'link', '') or '').strip()
            summary = (getattr(e, 'summary', '') or '').strip()
            blob = f"{title} {summary}"
            if not KEYWORDS.search(blob):
                continue
            when = parse_dt(e)
            if when and when < cutoff:
                continue
            if not link:
                continue
            cands.append({
                'title': title,
                'url': link,
                'source': src,
                'published': when.isoformat().replace('+00:00','Z') if when else None,
            })

    # naive dedupe by url
    seen = set()
    deduped = []
    for c in cands:
        if c['url'] in seen:
            continue
        seen.add(c['url'])
        deduped.append(c)

    # keep newest first when published known
    deduped.sort(key=lambda x: x['published'] or '', reverse=True)

    print(json.dumps(deduped[: args.limit], ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
