# ai-talent-graph

Academic AI scholar profiling tool — multi-source panoramic profiles using OpenAlex, arXiv, Semantic Scholar, and ORCID.

> OpenClaw Skill — works with [OpenClaw](https://github.com/openclaw/openclaw) AI agents

## What It Does

Builds comprehensive academic profiles of AI researchers by integrating four free public APIs: OpenAlex (papers/citations/institutions), Semantic Scholar (h-index/cross-validation), ORCID (career history), and arXiv (latest preprints). Optionally enriches profiles with GitHub engineering data and X/Twitter public influence metrics. Designed for academic research orientation — for recruitment use cases, see `ai-talent-radar`.

## Quick Start

```bash
# Install via ClawHub (recommended)
openclaw skill install ai-talent-graph

# Or clone this repo into your skills directory
git clone https://github.com/rrrrrredy/ai-talent-graph.git ~/.openclaw/skills/ai-talent-graph

# Install dependencies
bash scripts/setup.sh
```

## Features

- **4 academic data sources**: OpenAlex (primary), Semantic Scholar, ORCID, arXiv — all free public APIs
- **Scholar search**: Find researchers by topic with h-index and programming language filters
- **Full scholar profiles**: Papers, citations, h-index, institutional affiliations, career history
- **Institution analysis**: Browse top researchers at any organization (e.g., "DeepMind", "OpenAI")
- **Latest paper tracking**: Fetch recent arXiv preprints by research topic
- **GitHub integration**: Optional engineering profile enrichment with `GH_API_TOKEN`
- **X/Twitter influence**: Optional public influence metrics (followers, Bio) via guest token scraping
- **JSON output**: All commands support `--json` for programmatic processing
- **Compliance-first**: Only uses official free APIs, respects all rate limits

## Usage

```
"搜学者 做强化学习的"          → Search scholars in reinforcement learning
"查学者 @karpathy"            → Generate Andrej Karpathy's full profile
"查机构 DeepMind"             → List top researchers at DeepMind
"查最新 RLHF 论文"            → Fetch latest RLHF preprints from arXiv
"找做大模型的，h-index 要高"   → Search LLM scholars with high h-index
```

### CLI Examples

```bash
python3 talent_graph.py search "transformer" --limit 10 --hmin 15
python3 talent_graph.py profile "Yann LeCun" --github ylecun
python3 talent_graph.py institution "OpenAI" --limit 10
python3 talent_graph.py latest "AI agent autonomous" --limit 5
```

## Project Structure

```
ai-talent-graph/
├── SKILL.md                # Main skill definition
├── scripts/
│   ├── setup.sh            # Dependency installer
│   ├── talent_graph.py     # Main CLI entry point
│   ├── openalex_api.py     # OpenAlex API wrapper
│   ├── arxiv_api.py        # arXiv API wrapper
│   ├── semantic_scholar.py # Semantic Scholar API wrapper
│   ├── orcid_api.py        # ORCID API wrapper
│   └── github_api.py       # GitHub API wrapper
└── .gitignore
```

## Requirements

- [OpenClaw](https://github.com/openclaw/openclaw) agent runtime
- Python 3.8+
- `requests`
- Optional: `GH_API_TOKEN` environment variable for GitHub data (strongly recommended — raises rate limit from 60/hr to 5000/hr)

## License

[MIT](LICENSE)
