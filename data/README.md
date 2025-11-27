# Data Directory

## Files

### sample_fb_ads.csv
A small sample dataset (50 rows) for quick testing and development.

### Full Dataset
Place the full `synthetic_fb_ads_undergarments.csv` file in the project root directory.

## Data Schema

| Column | Type | Description |
|--------|------|-------------|
| campaign_name | string | Campaign name |
| adset_name | string | Ad set name |
| date | date | Date (YYYY-MM-DD) |
| spend | float | Ad spend in USD |
| impressions | int | Number of impressions |
| clicks | float | Number of clicks |
| ctr | float | Click-through rate |
| purchases | int | Number of purchases |
| revenue | float | Revenue in USD |
| roas | float | Return on ad spend |
| creative_type | string | Type of creative (Image, Video, UGC, Carousel) |
| creative_message | string | Ad creative message text |
| audience_type | string | Audience type (Broad, Lookalike, Retargeting) |
| platform | string | Platform (Facebook, Instagram) |
| country | string | Country code (US, UK, IN) |

## Data Quality Notes

- Some rows have missing values in spend, clicks, or revenue columns
- Date range: 2025-01-01 to 2025-03-31 (3 months)
- Total rows in full dataset: ~4,500

## Usage

### Use Sample Data (Fast)
Set in `config/config.yaml`:
```yaml
data:
  use_sample: true
```

### Use Full Data (Complete Analysis)
Set in `config/config.yaml`:
```yaml
data:
  use_sample: false
```
