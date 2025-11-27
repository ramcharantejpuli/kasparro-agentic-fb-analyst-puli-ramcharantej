# Agent Graph - Multi-Agent System Architecture

## Overview

The Kasparro Agentic Facebook Performance Analyst is a multi-agent system that autonomously diagnoses ad performance, identifies ROAS fluctuation drivers, and recommends creative improvements.

## Agent Roles & Responsibilities

### 1. Planner Agent
**Role:** Strategic decomposition of user queries into actionable subtasks

**Input:**
- User query (natural language)
- Dataset metadata (date range, available columns)

**Processing:**
- Parses user intent
- Identifies primary metrics (ROAS, CTR, revenue)
- Determines time periods (current vs comparison)
- Selects relevant segments for analysis
- Creates ordered task list with dependencies

**Output:**
- Structured analysis plan (JSON)
- Time period definitions
- Segment list
- Subtask sequence

**Example:**
```
Query: "Analyze ROAS drop in last 7 days"
→ Plan: Analyze ROAS for 2025-03-25 to 2025-03-31 vs 2025-03-18 to 2025-03-24
→ Segments: creative_type, platform, audience_type
→ Tasks: T1(data) → T2(insights) → T3(validate) → T4(creatives)
```

---

### 2. Data Agent
**Role:** Data loading, validation, and summarization

**Input:**
- Analysis plan from Planner
- CSV file path

**Processing:**
- Loads dataset with pandas
- Validates data quality (missing values, outliers)
- Filters by time periods
- Computes summary statistics (overall, by period, by segment)
- Detects anomalies using z-scores
- Calculates trends (% change, direction)

**Output:**
- Compact data summary (NOT full CSV)
- Data quality metrics
- Aggregated statistics by segment
- Trend indicators
- Anomaly flags

**Key Design Choice:** Returns summaries, not raw data, to keep context manageable for downstream agents.

---

### 3. Insight Agent
**Role:** Hypothesis generation using structured reasoning

**Input:**
- Analysis plan
- Data summary from Data Agent

**Processing:**
- Uses Think → Analyze → Conclude reasoning structure
- Identifies performance patterns across segments
- Generates 3-5 testable hypotheses
- Assigns initial confidence scores
- Considers multiple factors: creative fatigue, audience saturation, platform issues

**Output:**
- Structured hypotheses with reasoning chains
- Supporting evidence from data
- Initial confidence estimates (0-1)
- Affected segments
- Suggested validation methods

**Reasoning Example:**
```
THINK: Image ads show 25% CTR decline while Video maintained performance
ANALYZE: Image CTR: 0.0142 (current) vs 0.0189 (previous)
         Video CTR: 0.0175 vs 0.0178 (stable)
CONCLUDE: Image ads likely experiencing audience fatigue
```

---

### 4. Evaluator Agent
**Role:** Quantitative validation with statistical rigor

**Input:**
- Hypotheses from Insight Agent
- Raw data access for detailed analysis
- Analysis plan

**Processing:**
- Performs statistical tests (t-tests, correlation, ANOVA)
- Computes effect sizes (Cohen's d)
- Calculates confidence scores based on:
  - Statistical significance (p-values)
  - Effect size magnitude
  - Sample size adequacy
  - Segment specificity
- Implements retry logic for low-confidence results (<0.6)

**Output:**
- Validated hypotheses with confidence scores
- Statistical test results
- Quantitative evidence
- Actionability flags
- Retry recommendations

**Confidence Scoring:**
- 0.9-1.0: Very high (p<0.001, large effect, n>100)
- 0.7-0.9: High (p<0.01, medium effect, n>30)
- 0.5-0.7: Moderate (p<0.05, small effect, n>20)
- <0.5: Low (needs retry or more data)

---

### 5. Creative Generator Agent
**Role:** Data-driven creative recommendations

**Input:**
- Validated hypotheses
- Raw data for creative analysis
- Analysis plan

**Processing:**
- Identifies low-CTR segments (below threshold)
- Analyzes high-performing creative patterns:
  - Best creative types (Image, Video, UGC, Carousel)
  - Top messaging themes (urgency, value, social proof)
  - Effective CTAs
- Generates 4+ creative variations per segment:
  - Different messaging angles
  - Multiple formats
  - Specific copy (not templates)
- Grounds recommendations in data evidence

**Output:**
- Creative recommendations by segment
- Complete ad copy (headline, message, CTA)
- Rationale tied to data patterns
- Testing recommendations
- Expected impact estimates

**Creative Angles:**
- Urgency (limited time, deal ending)
- Value (quality, comfort, price)
- Social proof (reviews, ratings)
- Problem-solution (pain points)
- Risk reversal (guarantees)

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER QUERY                               │
│              "Analyze ROAS drop in last 7 days"                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
                ┌────────────────────┐
                │  PLANNER AGENT     │
                │                    │
                │ • Parse intent     │
                │ • Define periods   │
                │ • Select segments  │
                │ • Create task plan │
                └─────────┬──────────┘
                          │
                          │ Plan (JSON)
                          ▼
                ┌────────────────────┐
                │  DATA AGENT        │
                │                    │
                │ • Load CSV         │
                │ • Validate quality │
                │ • Compute stats    │
                │ • Detect anomalies │
                └─────────┬──────────┘
                          │
                          │ Data Summary
                          ▼
                ┌────────────────────┐
                │  INSIGHT AGENT     │
                │                    │
                │ • Think-Analyze-   │
                │   Conclude         │
                │ • Generate         │
                │   hypotheses       │
                │ • Initial scoring  │
                └─────────┬──────────┘
                          │
                          │ Hypotheses
                          ▼
                ┌────────────────────┐
                │  EVALUATOR AGENT   │
                │                    │
                │ • Statistical tests│
                │ • Confidence score │
                │ • Retry logic      │
                │ • Validate claims  │
                └─────────┬──────────┘
                          │
                          │ Validated Insights
                          ▼
                ┌────────────────────┐
                │  CREATIVE          │
                │  GENERATOR AGENT   │
                │                    │
                │ • Identify low-CTR │
                │ • Analyze patterns │
                │ • Generate copy    │
                │ • Test plan        │
                └─────────┬──────────┘
                          │
                          │ Creative Recommendations
                          ▼
                ┌────────────────────┐
                │  OUTPUTS           │
                │                    │
                │ • report.md        │
                │ • insights.json    │
                │ • creatives.json   │
                │ • logs/*.json      │
                └────────────────────┘
```

## Agent Communication Protocol

### Message Format
All inter-agent communication uses structured JSON with clear schemas.

### Error Handling
- Each agent logs inputs/outputs
- Errors propagate with context
- Retry logic at Evaluator level
- Graceful degradation (rule-based fallback)

### State Management
- Stateless agents (functional design)
- Workflow orchestrator manages state
- Logger tracks execution history

## Design Rationale

### Why Separate Agents?

1. **Planner:** Separates intent understanding from execution
2. **Data Agent:** Isolates data quality concerns, provides clean summaries
3. **Insight Agent:** Focuses on hypothesis generation with structured reasoning
4. **Evaluator:** Adds quantitative rigor, prevents false positives
5. **Creative Generator:** Specializes in actionable recommendations

### Key Design Choices

1. **Data Summaries, Not Raw Data:** Keeps context manageable, forces aggregation thinking
2. **Confidence Scoring:** Quantifies uncertainty, enables filtering
3. **Retry Logic:** Improves robustness, handles edge cases
4. **Structured Reasoning:** Makes agent thinking transparent and debuggable
5. **Rule-Based Fallback:** Works without LLM API, demonstrates architecture

## Validation Layer

The Evaluator Agent implements a multi-level validation approach:

1. **Statistical Validation:** t-tests, effect sizes, p-values
2. **Sample Size Checks:** Ensures adequate data for conclusions
3. **Segment Specificity:** Confirms patterns are segment-specific, not global
4. **Confidence Calibration:** Maps evidence strength to 0-1 scores
5. **Retry Mechanism:** Re-analyzes low-confidence hypotheses

## Extensibility

The architecture supports:
- Adding new agents (e.g., Budget Optimizer, Audience Expander)
- Swapping implementations (rule-based ↔ LLM-powered)
- Custom validation rules
- Alternative data sources
- Multi-step reasoning chains

## Performance Considerations

- **Latency:** Sequential execution (~10-30s total)
- **Cost:** Rule-based = $0, LLM-powered = ~$0.10-0.50 per run
- **Scalability:** Handles datasets up to 100K rows efficiently
- **Memory:** Peak ~500MB for large datasets

## Future Enhancements

1. **Parallel Execution:** Run independent agents concurrently
2. **Memory Layer:** Store insights across runs for learning
3. **LLM Integration:** Replace rule-based logic with GPT-4
4. **Real-time Mode:** Stream results as agents complete
5. **Interactive Mode:** Allow user feedback mid-workflow
