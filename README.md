# Decoding Customer Value — SQL-Driven Retention Strategy

A comprehensive customer intelligence project for a D2C fashion brand, analyzing 3,900 customers across behavioral, transactional, and promotional dimensions to build a data-backed retention strategy.

## Project Overview

**Problem:** The brand has data but no intelligence. It cannot answer who its loyal customers are, whether its promo program builds loyalty or attracts bargain hunters, or which geographies have organic demand.

**Approach:** Build engineered loyalty metrics from raw data, segment customers via SQL queries, visualize insights in an interactive dashboard, and deliver actionable business recommendations.

**Key Constraint:** No timestamps, no loyalty labels — every metric must be constructed from 18 available variables.

## Deliverables

| Deliverable | File | Description |
|---|---|---|
| **Data Preparation** | `01_data_preparation.py` | Cleans data, engineers 8 features with full justification |
| **Enriched Dataset** | `customer_features.csv` | 3,900 customers × 26 columns (18 original + 8 engineered) |
| **SQL Database** | `customer_intel.db` | SQLite database with all customer features |
| **Segmentation Queries** | `02_segmentation.sql` | 12+ SQL queries answering 5 core business questions |
| **Dashboard Data** | `03_dashboard/dashboard_data.json` | Pre-computed JSON for visualization |
| **Interactive Dashboard** | `03_dashboard/index.html` | 4-panel Chart.js dashboard (open in browser) |
| **Retention Playbook** | `04_playbook.md` | Promo sunset plan + ideal customer profile + exec summary |
| **Feature Analysis** | `feature_correlations.csv` | Correlation matrix of all engineered features |
| **Loyalty Comparison** | `loyalty_comparison.csv` | Score A vs Score B vs Score C comparison |

## Quick Start

### Prerequisites
- Python 3.10+
- pandas, scikit-learn, numpy (for data preparation)
- SQLite (bundled with Python)
- A modern web browser (for dashboard)

### Step 1: Data Preparation
```bash
python 01_data_preparation.py
```
Outputs: `customer_features.csv`, `feature_correlations.csv`, `loyalty_comparison.csv`

### Step 2: Database Setup & Queries
```bash
python 02_db_setup.py
```
Creates `customer_intel.db` and executes all segmentation queries.

### Step 3: Generate Dashboard Data
```bash
python 03_generate_dashboard_data.py
```
Outputs: `03_dashboard/dashboard_data.json`

### Step 4: Build inline Dashboard
```bash
python 03_build_inline.py
```

### Step 5: View Dashboard
Open `03_dashboard/index.html` in your browser. The dashboard loads data from the JSON file.

## Engineered Features

| Feature | Type | Business Purpose |
|---|---|---|
| `loyalty_score_a` | 0–100 | Frequency-based loyalty (how often) |
| `loyalty_score_b` | 0–100 | Value-based loyalty (how much) |
| `loyalty_score_c` | 0–100 | Hybrid ensemble (balanced view) |
| `promo_dependency_score` | 0–100 | Reliance on discounts |
| `value_tier` | Category | Platinum / Gold / Silver / Bronze |
| `satisfaction_flag` | Category | Satisfied / Neutral / At Risk |
| `category_affinity` | Category | Preferred product category |
| `seasonal_breadth` | 1–4 | Number of seasons engaged |

## SQL Segmentation Queries

The SQL file contains 12+ queries organized by business question:

1. **Q1:** Customer Loyalty vs Promo Dependency Segments (4-segment matrix)
2. **Q2:** High-Value vs Low-Value Customer Profiles (quartile comparison)
3. **Q3:** Geographic Opportunity Analysis (20 states ranked by organic pull)
4. **Q4:** Promo Impact by Value Tier (revenue at risk analysis)
5. **Q5:** Ideal Customer Profile (demographic + behavioral + transactional)
6. **Pareto:** Revenue concentration analysis
7. **Category × Tier:** Cross-tab of categories by value tier
8. **Season × Tenure:** Seasonal engagement patterns
9. **Loyalty Comparison:** Score A vs B vs C segment overlap
10. **Payment × Tier:** Payment preferences by value tier
11. **At-Risk Profile:** Low-satisfaction customer analysis

## Dashboard Panels

| Panel | Chart Type | What It Shows |
|---|---|---|
| **Customer Pyramid** | Bar + Line | Tier distribution + revenue contribution |
| **Promo vs Retention** | Scatter | Promo dependency vs loyalty (color = tier) |
| **Geographic Opportunity** | Horizontal Bar | Top 15 states by organic opportunity score |
| **Category Funnel** | Bar + Line | Categories ranked by retention signal |

## Key Findings

- **49.4% of customers are organic or semi-organic buyers** — the brand has real loyalty
- **Top 20% generate only 31% of revenue** — flat distribution, broad retention needed
- **17.4% are at-risk** (low satisfaction) — highest-ROI retention target
- **Arizona, Kansas, Alaska** are top organic opportunity states
- **Gold tier no-promo buyers** are the safest first target for promo sunset

## File Structure

```
sql-driven-retention-strategy/
├── README.md
├── data/
│   ├── Dataset.csv
│   ├── customer_features.csv
│   ├── feature_correlations.csv
│   └── loyalty_comparison.csv
├── python/
│   ├── 01_data_preparation.py
│   ├── 02_db_setup.py
│   └── 03_generate_dashboard_data.py
├── sql/
│   └── 02_segmentation.sql
├── database/
│   └── customer_intel.db
├── dashboard/
│   ├── index.html
│   └── dashboard_data.json
├── playbook/
│   └── 04_playbook.md
└── documentation/
    ├── PS.pdf
    └── PS.txt
```

## Technology Stack

- **Python 3.13** — Data preparation and feature engineering
- **pandas / scikit-learn / numpy** — Data manipulation and clustering
- **SQLite** — Query layer (portable, zero-dependency)
- **Chart.js** — Interactive dashboard visualization
- **HTML/CSS/JS** — Static dashboard (no server required)

---

*Project: Decoding Customer Value — SQL-Driven Retention Strategy*
