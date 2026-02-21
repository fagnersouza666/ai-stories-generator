# AI Stories Generator

Automated pipeline for curating AI/tech news and generating Instagram Stories (1080×1920).

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

This OpenClaw skill automates the entire workflow of:
1. **Curating** AI/tech news from RSS feeds (Hacker News, TechCrunch, etc.)
2. **Filtering** by keywords, recency (last N hours), and deduplication
3. **Generating** visual Instagram Stories with screenshot backgrounds and text overlays

Perfect for content creators, developers, and marketers running scheduled social media automation (e.g., 3 Stories/day).

## Features

- 📰 **RSS News Curation** - Filter by AI/tech keywords from multiple feeds
- 🎨 **Visual Story Generation** - 1080×1920 PNG with screenshot backgrounds
- ⏰ **Automation-Ready** - Designed for cron scheduling
- 🔧 **Customizable** - Edit keywords, fonts, colors, overlay styles

## Quick Start

### Installation

```bash
# Clone this repo
git clone https://github.com/yourusername/ai-stories-generator.git
cd ai-stories-generator

# Install dependencies
pip install playwright pillow feedparser
playwright install chromium
```

### Usage

**1. Curate news from RSS feeds**

Create a `feeds.txt` file:
```
https://hnrss.org/newest?q=AI
https://techcrunch.com/category/artificial-intelligence/feed/
```

Run curation:
```bash
python scripts/pick_ai_news.py \
    --feeds feeds.txt \
    --hours 24 \
    --limit 15 > candidates.json
```

**2. Select top 3 and create `items.json`**

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

**3. Generate Stories**

```bash
python scripts/gen_stories_from_urls.py \
    --items items.json \
    --shots-dir shots/ \
    --out-dir out/
```

**Output**: 3 Instagram-ready Stories in `out/` (1080×1920 PNG)

## Automation Example

**Cron schedule** (9:00, 13:00, 18:00):
```cron
0 9,13,18 * * * cd /path/to/ai-stories-generator && ./run_stories.sh
```

## OpenClaw Skill

This is an [OpenClaw AgentSkill](https://openclaw.ai). To use it with OpenClaw:

1. Package the skill: `openclaw skill package .`
2. Install: `openclaw skill install ai-stories-generator.skill`
3. Use: The agent will automatically trigger when working with Instagram Stories or news curation tasks

## Customization

- **Keywords**: Edit `KEYWORDS` regex in `scripts/pick_ai_news.py`
- **Story Layout**: Adjust fonts, colors in `scripts/make_story.py`
- **Viewport**: Change aspect ratio in `scripts/gen_stories_from_urls.py`

## License

MIT © Fagner Souza

## Contributing

Contributions welcome! Open an issue or PR.

---

**Built with**: Python, Playwright, Pillow, OpenClaw
