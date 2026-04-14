---
name: ai-talent-graph
description: "Academic research-oriented AI scholar profiling tool integrating OpenAlex, arXiv, Semantic Scholar, ORCID free APIs, with optional X/Twitter public influence data. Triggers: search scholar, find expert, AI talent graph, analyze institution, find LLM researchers, latest papers, academic graph, paper tracing, research direction analysis, check scholar twitter, X account influence. Not for: recruitment-oriented analysis (use ai-talent-radar); precise Chinese scholar search (data sources are primarily English)."
tags: [talent, academic, research, scholar, openalex, arxiv, twitter, x]
metadata:
  version: "V7"
---

# AI Talent Graph V7 🕸️

## First-time Setup

Run the dependency check script before first use:
```bash
bash scripts/setup.sh
```
> The agent will auto-run this on first trigger; manual execution is usually unnecessary.

Integrates **OpenAlex, arXiv, Semantic Scholar, ORCID** multi-source free APIs to build comprehensive AI scholar profiles.

---

## Quick Start

**Step 1: Install dependencies**
```bash
pip install requests
```

**Step 2: Locate script directory**
```bash
SKILL_DIR=$(dirname "$(find . -name "talent_graph.py" -type f 2>/dev/null | head -1)")
echo "Script directory: $SKILL_DIR"
```

**Step 3: Verify**
```bash
cd "$SKILL_DIR" && python3 talent_graph.py search "transformer" --limit 3
```
You should see a list of scholars.

> **GitHub Token (optional, strongly recommended)**: Enables automatic GitHub engineering data in profiles and raises API limit from 60/hour to 5000/hour.
> ```bash
> export GH_API_TOKEN="your_personal_access_token"
> ```

---

## Scenario Mapping

| User says | Agent executes |
|-----------|---------------|
| Search scholars in reinforcement learning | `cd $SKILL_DIR && python3 talent_graph.py search "reinforcement learning"` |
| Find LLM researchers with high h-index | `cd $SKILL_DIR && python3 talent_graph.py search "large language model" --hmin 20` |
| Find Python-based Agent researchers | `cd $SKILL_DIR && python3 talent_graph.py search "AI agent" --lang python` |
| Profile @karpathy | `cd $SKILL_DIR && python3 talent_graph.py profile "Andrej Karpathy" --github karpathy` |
| Analyze DeepMind | `cd $SKILL_DIR && python3 talent_graph.py institution "DeepMind"` |
| Latest RLHF papers | `cd $SKILL_DIR && python3 talent_graph.py latest "RLHF reinforcement learning human feedback"` |
| Output JSON for further processing | Add `--json` to any command |
| Check scholar X/Twitter influence (followers/Bio) | Use any X/Twitter scraping tool to fetch profile for the scholar's handle |
| Check scholar's latest tweets | Use any X/Twitter scraping tool to fetch timeline for the scholar's handle |

> **Note**: Data sources are primarily English academic databases. Search domestic institutions using English names (e.g., ByteDance / Tsinghua University).

---

## Execution Guide

### Search Scholars
```bash
cd $SKILL_DIR
python3 talent_graph.py search "multimodal large language model" --limit 10 --hmin 15 --lang python
```
- `--hmin`: Minimum h-index threshold
- `--lang`: Programming language filter (requires GH_API_TOKEN for GitHub data)
- `--limit`: Max results (default 10, max 20)

### Generate Scholar Profile
```bash
python3 talent_graph.py profile "Yann LeCun" --github ylecun
```
- `--github`: Optional, provide GitHub username for engineering data
- Without it, the system **auto-guesses** lowercase/no-space name variants (marked "unverified")

### Supplement X/Twitter Data (optional, no login needed)

After generating a scholar profile, if you know the scholar's X/Twitter handle, supplement community influence data:

```bash
# Use any X/Twitter scraping tool to fetch: followers, Bio, tweet count
# Example handles: karpathy (Andrej Karpathy), ylecun (Yann LeCun), gdb (Greg Brockman)
```

> ⚠️ If direct access to x.com is blocked, set `HTTP_PROXY` environment variable. Unknown handles can often be found on scholar homepages or Google Scholar profiles.

### Query Institution
```bash
python3 talent_graph.py institution "OpenAI" --limit 10
```

### Track Latest Papers (arXiv)
```bash
python3 talent_graph.py latest "AI agent autonomous" --limit 5
```
Returns recent arXiv preprints with abstracts and PDF links. arXiv enforces 3-second rate limiting; expect 5-10 second wait.

---

## Error Handling

| Error | Resolution |
|-------|-----------|
| ModuleNotFoundError: requests | Run `pip install requests` |
| ImportError module not found | Confirm you `cd $SKILL_DIR` before running; don't call from other directories |
| OpenAlex returns empty results | Hint: No matching scholars found; try English keywords |
| GitHub API 403 / rate limit | Hint: GitHub requests exhausted; configure GH_API_TOKEN; academic data only shown |
| ORCID timeout | Graceful degradation: returns OpenAlex data only, notes "ORCID data unavailable" |
| All data sources fail | Clearly state: data sources temporarily unavailable, please retry later |

---

## Data Sources

| Platform | Data Dimensions | Free Quota | Notes |
|----------|----------------|------------|-------|
| OpenAlex | Scholar/Paper/Citation/Institution | Unlimited (reasonable rate) | Primary source |
| Semantic Scholar | h-index/Citations | 100 req/5min | Cross-validation supplement |
| ORCID | Scholar profile/Employment history | Unlimited | Identity supplement |
| arXiv | Preprint papers | Unlimited (3s interval) | `latest` command only |
| GitHub | Projects/Tech stack | 60/hour (no token) | Stable with token configured |

---

## Compliance

- Only uses official free public APIs, respects all platform rate limits
- No scraping, no anti-bot circumvention
- Data is for academic research and talent evaluation reference only

---

### Gotchas

⚠️ OpenAlex access may occasionally time out from certain regions → `timeout=15s` set, auto-retry once on failure, graceful degradation on second failure

⚠️ Semantic Scholar API rate limit 100 req/5min, batch queries trigger 429 → 3s sleep between requests; 60s backoff on 429

⚠️ GitHub API without Token is limited to 60 req/hour, batch querying multiple scholars exhausts quota → strongly recommend configuring `GH_API_TOKEN`; without Token, query at most 3 scholars

⚠️ ORCID search yields no results for Chinese names (database is primarily English) → hint users to use English full names (First Last) or ORCID ID directly

⚠️ arXiv enforces 3s request interval, consecutive calls trigger 429 → `latest` command caps at 5 papers per batch with 3s sleep between requests

⚠️ If `cd $SKILL_DIR` fails (path not found), running `python3 talent_graph.py` directly causes ImportError → must confirm path via Quick Start Step 2 first

---

### Hard Stop

**If the same tool call fails more than 3 times, stop immediately.** List all failed approaches and reasons, mark **"Manual intervention needed"**, and wait for human confirmation.

---

## Changelog

### V7
- Added X/Twitter scholar influence dimension: supplement followers, Bio, tweet count after profile generation
- Added X/Twitter trigger words in description
- Tags: added `twitter`, `x`
- Scenario mapping: added X query scenarios

### V6
- Synced H1 title version with frontmatter

### V5
- Single-line description (YAML compatible), added "not applicable" scenarios
- Added `tags`
- Synced scripts/ to latest versions
- API endpoints, quotas, compliance integrated into SKILL.md

### V4
- Integrated OpenAlex, arXiv, Semantic Scholar, ORCID four data sources
- Differentiated academic research orientation from recruitment orientation (ai-talent-radar)
- Added institution query and latest paper tracking
- Added optional GitHub Token configuration

### V1-V3
- Initial: OpenAlex + arXiv dual data sources
- Progressive expansion with Semantic Scholar, ORCID supplements
