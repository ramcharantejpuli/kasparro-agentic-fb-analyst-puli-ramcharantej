# Kasparro Agentic Facebook Performance Analyst

An autonomous multi-agent system that diagnoses Facebook Ads performance, identifies ROAS fluctuation drivers, and recommends creative improvements using quantitative analysis and creative messaging data.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      User Query                              │
│           "Analyze ROAS drop in last 7 days"                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
            ┌────────────────┐
            │ Planner Agent  │ ← Decomposes query into subtasks
            └────────┬───────┘
                     │
                     ▼
            ┌────────────────┐
            │  Data Agent    │ ← Loads & summarizes dataset
            └────────┬───────┘
                     │
                     ▼
            ┌────────────────┐
            │ Insight Agent  │ ← Generates hypotheses
            └────────┬───────┘
                     │
                     ▼
            ┌────────────────┐
            │ Evaluator      │ ← Validates hypotheses quantitatively
            │    Agent       │    (confidence scoring, retry logic)
            └────────┬───────┘
                     │
                     ▼
            ┌────────────────┐
            │   Creative     │ ← Generates new creative messages
            │  Generator     │    for low-CTR campaigns
            └────────┬───────┘
                     │
                     ▼
            ┌────────────────┐
            │ Final Report   │ ← Markdown report + JSON outputs
            └────────────────┘
```

## Quick Start

### Prerequisites
- Python >= 3.10
- OpenAI API key (or compatible LLM endpoint)

### Installation

```bash
# Clone repository
git clone <repo-url>
cd kasparro-agentic-fb-analyst

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Linux/Mac)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

1. Set your OpenAI API key:
```bash
# Windows
set OPENAI_API_KEY=your-key-here

# Linux/Mac
export OPENAI_API_KEY=your-key-here
```

2. Edit `config/config.yaml` to adjust settings:
```yaml
data:
  csv_path: "synthetic_fb_ads_undergarments.csv"
  use_sample: false  # Set to true for quick testing

analysis:
  confidence_min: 0.6
  lookback_days: 7
  
model:
  name: "gpt-4o-mini"
  temperature: 0.7
  
random_seed: 42
```

### Data Setup

Place the full dataset at the root:
```
synthetic_fb_ads_undergarments.csv
```

Or use the sample dataset in `data/sample_fb_ads.csv` for testing.

### Run Analysis

```bash
# Using Python directly
python src/run.py "Analyze ROAS drop in last 7 days"

# Or using make
make run QUERY="Analyze ROAS drop in last 7 days"
```

### Run Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Or using make
make test
```

## Outputs

After running, check these files:

- `reports/report.md` - Human-readable analysis report
- `reports/insights.json` - Structured hypotheses with confidence scores
- `reports/creatives.json` - Creative recommendations for low-CTR campaigns
- `logs/` - Detailed execution traces (JSON format)

## Agent Roles

### 1. Planner Agent
- Decomposes user query into actionable subtasks
- Determines analysis scope (time periods, metrics, segments)
- Outputs structured plan in JSON format

### 2. Data Agent
- Loads and validates dataset
- Computes summary statistics and aggregations
- Identifies data quality issues
- Returns compact data summaries (not full CSV)

### 3. Insight Agent
- Generates hypotheses explaining performance patterns
- Uses Think → Analyze → Conclude reasoning structure
- Considers multiple factors: creative fatigue, audience saturation, platform changes
- Outputs hypotheses with initial confidence estimates

### 4. Evaluator Agent
- Validates each hypothesis quantitatively
- Computes statistical evidence (correlations, trends, comparisons)
- Assigns confidence scores (0-1 scale)
- Implements retry logic for low-confidence results
- Filters and ranks insights

### 5. Creative Generator Agent
- Identifies low-CTR campaigns needing improvement
- Analyzes existing high-performing creative messages
- Generates new creative variations (headlines, CTAs, messaging angles)
- Ensures recommendations are data-driven and contextual

## Validation Layer

The system includes multiple validation mechanisms:

1. **Confidence Scoring**: Each hypothesis receives a 0-1 confidence score based on:
   - Statistical significance of evidence
   - Data quality and completeness
   - Consistency across segments

2. **Retry Logic**: Low-confidence insights (<0.6) trigger:
   - Re-analysis with different parameters
   - Alternative hypothesis generation
   - Additional data validation

3. **Quantitative Checks**:
   - Trend analysis (regression, correlation)
   - Segment comparisons (t-tests, effect sizes)
   - Anomaly detection (z-scores, IQR)

## Project Structure

```
kasparro-agentic-fb-analyst/
├── README.md
├── requirements.txt
├── Makefile
├── config/
│   └── config.yaml
├── src/
│   ├── run.py                    # Main orchestration
│   ├── agents/
│   │   ├── planner.py
│   │   ├── data_agent.py
│   │   ├── insight_agent.py
│   │   ├── evaluator.py
│   │   └── creative_generator.py
│   ├── orchestrator/
│   │   └── workflow.py
│   └── utils/
│       ├── config_loader.py
│       ├── logger.py
│       └── data_utils.py
├── prompts/
│   ├── planner_prompt.md
│   ├── data_agent_prompt.md
│   ├── insight_agent_prompt.md
│   ├── evaluator_prompt.md
│   └── creative_generator_prompt.md
├── data/
│   ├── README.md
│   └── sample_fb_ads.csv
├── logs/
│   └── .gitkeep
├── reports/
│   └── .gitkeep
└── tests/
    ├── test_evaluator.py
    └── test_agents.py
```

## Example Output

### Insights (insights.json)
```json
{
  "hypotheses": [
    {
      "id": "H1",
      "hypothesis": "ROAS declined due to creative fatigue in Image ads",
      "confidence": 0.85,
      "evidence": {
        "metric": "CTR decline",
        "value": "-32%",
        "segment": "Image creative_type"
      }
    }
  ]
}
```

### Creatives (creatives.json)
```json
{
  "recommendations": [
    {
      "campaign": "Men ComfortMax Launch",
      "current_ctr": 0.012,
      "new_creatives": [
        {
          "message": "Limited time: Premium comfort at 30% off",
          "rationale": "Urgency + value proposition"
        }
      ]
    }
  ]
}
```

## Development

### Setup Development Environment
```bash
make setup
```

### Run Linting
```bash
make lint
```

### Clean Generated Files
```bash
make clean
```

## Design Choices

See the [self-review PR](../../pull/1) for detailed discussion of:
- Agent separation rationale
- Prompt engineering strategies
- Validation approach
- Trade-offs and limitations

## Release

Current version: **v1.0**

## License

MIT
