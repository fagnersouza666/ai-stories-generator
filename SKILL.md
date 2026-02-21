---
name: ai-stories-generator
description: Automated AI news curation and Instagram Stories generation (1080x1920). Curate AI/tech news from RSS feeds, filter by recency and keywords, generate visual Stories with screenshot backgrounds and text overlays. Use when: (1) Creating Instagram/social media Stories about AI/tech news, (2) Automating content curation from RSS feeds, (3) Generating visual content at scale (3x/day workflows), (4) Building news aggregation pipelines with visual output.
---

# AI Stories Generator

Automated pipeline for curating AI/tech news from RSS feeds and generating Instagram Stories (1080×1920) with screenshot backgrounds and text overlays.

## What This Skill Provides

1. **RSS News Curation** - Filter AI/tech news from multiple feeds by keywords, recency (last N hours), and deduplication
2. **Visual Story Generation** - Create Instagram-ready Stories (1080×1920) with:
   - Screenshot backgrounds captured from article URLs
   - Text overlays with title, subtitle, and impact text
   - Professional composition using Pillow
3. **Automation-Ready** - Designed for cron scheduling (e.g., 3x/day content generation)

## Core Workflow

```bash
# 1. Curate news from RSS feeds (last 24h, AI-related, top 15)
python scripts/pick_ai_news.py \
    --feeds feeds.txt \
    --hours 24 \
    --limit 15 > candidates.json

# 2. Generate Stories from top 3 URLs
python scripts/gen_stories_from_urls.py \
    --items items.json \
    --shots-dir shots/ \
    --out-dir out/
```

## Scripts

### `pick_ai_news.py` - RSS News Curation

Filters news from RSS feeds by keywords, recency, and deduplication.

**Input**: Text file with feed URLs (one per line, `#` for comments)  
**Output**: JSON array `[{title, url, source, published}]`

**Keywords** (case-insensitive): `ai`, `artificial intelligence`, `llm`, `agent`, `copilot`, `gemini`, `openai`, `anthropic`, `deepmind`, `model`, `inference`, `training`, `chip`, `gpu`, `nvidia`

**Usage**:
```bash
python scripts/pick_ai_news.py \
    --feeds feeds.txt \
    --hours 24 \
    --limit 15
```

**Arguments**:
- `--feeds` (required): Path to feeds file
- `--hours` (default: 24): Filter entries from last N hours
- `--limit` (default: 15): Max candidates to return

**Example feeds file**:
```
https://hnrss.org/newest?q=AI
https://news.ycombinator.com/rss
# TechCrunch AI
https://techcrunch.com/category/artificial-intelligence/feed/
```

---

### `gen_stories_from_urls.py` - Story Generation

Captures screenshots from URLs and generates final Stories with text overlays.

**Input**: JSON with `[{title, url, subtitle, impact}]`  
**Output**: 1080×1920 PNG files (Instagram Stories format)

**Workflow**:
1. Opens each URL in Playwright (headless browser)
2. Captures screenshot "above the fold" (viewport 1080×1920, no scroll)
3. Calls `make_story.py` to compose final Story (background + text overlay)
4. Saves to `--out-dir`

**Usage**:
```bash
python scripts/gen_stories_from_urls.py \
    --items items.json \
    --shots-dir shots/ \
    --out-dir out/
```

**Arguments**:
- `--items` (default: `items.json`): Input JSON file
- `--shots-dir` (default: `shots/`): Where to save screenshots
- `--out-dir` (default: `out/`): Where to save final Stories
- `--browser` (default: `chromium`): Browser type (`chromium`, `firefox`, `webkit`)
- `--timeout` (default: 30000): Page load timeout (ms)
- `--skip-screenshots`: Reuse existing screenshots (faster iteration)

**Example `items.json`**:
```json
[
  {
    "title": "OpenAI Releases GPT-5",
    "url": "https://techcrunch.com/...",
    "subtitle": "Multimodal reasoning breakthrough",
    "impact": "Game changer for AI agents"
  }
]
```

**Dependencies**:
```bash
pip install playwright pillow feedparser
playwright install chromium
```

---

### `make_story.py` - Story Compositor

Composes final Story: screenshot background + darkened overlay + centered text.

**Input**: Screenshot PNG + text fields  
**Output**: Final 1080×1920 Story PNG

**Usage** (typically called by `gen_stories_from_urls.py`):
```bash
python scripts/make_story.py \
    --bg shots/shot_01.png \
    --title "OpenAI Releases GPT-5" \
    --subtitle "Multimodal reasoning" \
    --impact "Game changer" \
    --out out/story_01.png
```

## Automation Example (3x/day)

**Cron schedule** (9:00, 13:00, 18:00 BRT):
```cron
0 9,13,18 * * * cd /path/to/project && ./run_stories.sh
```

**`run_stories.sh`**:
```bash
#!/bin/bash
set -e

# 1. Curate news
python scripts/pick_ai_news.py \
    --feeds feeds.txt \
    --hours 24 \
    --limit 15 > candidates.json

# 2. Pick top 3 (manual or via LLM scoring)
# ... selection logic ...

# 3. Generate Stories
python scripts/gen_stories_from_urls.py \
    --items items.json \
    --out-dir out/

# 4. Send to Telegram/Instagram (optional)
# ... delivery logic ...
```

## Customization

- **Keywords**: Edit `KEYWORDS` regex in `pick_ai_news.py`
- **Story Layout**: Adjust fonts, colors, overlay opacity in `make_story.py`
- **Viewport Size**: Change `VIEWPORT_W`/`VIEWPORT_H` in `gen_stories_from_urls.py` for different aspect ratios

## Common Issues

**"playwright not found"**: Run `pip install playwright && playwright install chromium`  
**Empty screenshots**: Increase `--timeout` or check if URL requires authentication  
**Stories look cluttered**: Shorten `title`/`subtitle` fields or adjust font size in `make_story.py`
