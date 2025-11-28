# Kasparro — Agentic Facebook Performance Analyst

## Quick Start
```bash
python -V  # should be >= 3.10
python -m venv .venv && source .venv/bin/activate  # win: .venv\Scripts\activate
pip install -r requirements.txt
python src/run.py "Analyze ROAS drop in last 7 days"
```

## Data
- Place the full CSV locally: `synthetic_fb_ads_undergarments.csv` in project root
- Or copy a small sample to `data/sample_fb_ads.csv`
- See `data/README.md` for details

## Config
Edit `config/config.yaml`:
```yaml
python: "3.10"
random_seed: 42
confidence_min: 0.6
use_sample_data: false
```

## Repo Map
- `src/agents/` — planner.py, data_agent.py, insight_agent.py, evaluator.py, creative_generator.py
- `prompts/` — *.md prompt files with variable placeholders
- `reports/` — report.md, insights.json, creatives.json
- `logs/` — json traces
- `tests/` — test_evaluator.py

## Run
```bash
make run  # or: python src/run.py "Analyze ROAS drop"
```

## Outputs
- `reports/report.md`
- `reports/insights.json`
- `reports/creatives.json`

## Observability
- JSON logs in `logs/` directory with agent execution traces

## Release
- Tag: `v1.0`
- Link: https://github.com/ramcharantejpuli/kasparro-agentic-fb-analyst-puli-ramcharantej/releases/tag/v1.0

## Self-Review
- See `SELF_REVIEW.md` for design choices & tradeoffs
- PR: Create "self-review" branch describing design decisions

---

## Architecture Diagram

```
User Query → Planner → Data Agent → Insight Agent → Evaluator → Creative Generator → Reports
```

## Agent Roles & Validation

See `agent_graph.md` for detailed architecture and `SELF_REVIEW.md` for design choices.

**Key Features:**
- 5 specialized agents (Planner, Data, Insight, Evaluator, Creative Generator)
- Statistical validation with confidence scoring (0-1 scale)
- Think → Analyze → Conclude reasoning structure
- Retry logic for low-confidence results (<0.6)
- LLM integration with rule-based fallback

## Example Outputs

### insights.json
```json
{
  "hypotheses": [{
    "id": "H1",
    "hypothesis": "ROAS declined due to creative fatigue",
    "confidence": 0.85,
    "evidence": {"metric": "CTR decline", "value": "-32%"}
  }]
}
```

### creatives.json
```json
{
  "recommendations": [{
    "campaign": "Men ComfortMax Launch",
    "new_creatives": [{"message": "Limited time: 30% off"}]
  }]
}
```
