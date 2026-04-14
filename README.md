# ai-talent-graph

Academic research-oriented AI scholar profiling tool integrating OpenAlex, arXiv, Semantic Scholar, ORCID free APIs, with optional X/Twitter public influence data.

An [OpenClaw](https://github.com/openclaw/openclaw) Skill for building comprehensive AI scholar profiles from multiple public academic data sources.

## Installation

### Option A: OpenClaw (recommended)
```bash
# Clone to OpenClaw skills directory
git clone https://github.com/rrrrrredy/ai-talent-graph ~/.openclaw/skills/ai-talent-graph

# Run setup (installs Python dependencies)
bash ~/.openclaw/skills/ai-talent-graph/scripts/setup.sh
```

### Option B: Standalone
```bash
git clone https://github.com/rrrrrredy/ai-talent-graph
cd ai-talent-graph
bash scripts/setup.sh
```

## Dependencies

### Python packages
- `requests`

### Other Skills (optional)
- None (X/Twitter data can be supplemented with any X scraping tool)

## Usage

### Search scholars by research topic
```bash
cd scripts/
python3 talent_graph.py search "multimodal large language model" --limit 10 --hmin 15
```

### Generate a scholar profile
```bash
python3 talent_graph.py profile "Yann LeCun" --github ylecun
```

### Analyze an institution
```bash
python3 talent_graph.py institution "OpenAI" --limit 10
```

### Track latest arXiv papers
```bash
python3 talent_graph.py latest "AI agent autonomous" --limit 5
```

### Output as JSON
```bash
python3 talent_graph.py search "transformer" --json
```

## Data Sources

| Platform | Data | Free Quota |
|----------|------|------------|
| OpenAlex | Scholar/Paper/Citation/Institution | Unlimited (reasonable rate) |
| Semantic Scholar | h-index/Citations | 100 req/5min |
| ORCID | Scholar profiles/Employment | Unlimited |
| arXiv | Preprint papers | Unlimited (3s interval) |
| GitHub | Projects/Tech stack | 60/hr (no token), 5000/hr (with token) |

## Project Structure

```
ai-talent-graph/
├── SKILL.md              # Main skill definition
├── scripts/
│   ├── setup.sh          # Installation script
│   ├── talent_graph.py   # Main entry point
│   ├── openalex_api.py   # OpenAlex API wrapper
│   ├── arxiv_api.py      # arXiv API wrapper
│   ├── orcid_api.py      # ORCID API wrapper
│   ├── semantic_scholar.py # Semantic Scholar API wrapper
│   └── github_api.py     # GitHub API wrapper
└── README.md
```

## License

MIT
