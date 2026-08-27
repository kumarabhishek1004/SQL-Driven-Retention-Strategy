# Decoding Customer Value — Retention Playbook

## Executive Summary (1 Page)

**The Core Question:** Is the brand building a loyal customer base, or is it reliant on continuous promotional activity?

**Verdict: The brand is building loyalty — but also over-investing in promos that erode margins.**

### Key Findings

1. **49.4% of customers are organic or semi-organic buyers** (Organic Loyal 24.2% + Loyal but Promo-Sensitive 25.2%). These two segments drive **54.2% of total revenue** ($126,282) without requiring full discount dependency. The brand has a real loyalty foundation.

2. **Promo dependency is evenly distributed across tiers — a structural problem.** Platinum customers have 48.3% promo use vs. 51.7% no-promo. This means even the best customers are split. The promo program is not segmenting well — it's blanket discounting everyone.

3. **Top 20% of customers generate only 31% of revenue** (Pareto analysis). This is a flat distribution — the brand lacks a strong "whale" tier. Revenue is spread thin, making every customer loss impactful.

4. **17.4% of customers are "At Risk"** (rating < 3.0), generating $39,786 in revenue. These customers have moderate loyalty (score 39.4) but low satisfaction — a retention intervention here could save significant revenue.

5. **Geographic opportunity is real but untapped.** Arizona, Kansas, Alaska, and Tennessee show high organic opportunity scores (39–44) with low promo dependency, suggesting genuine brand pull in these markets without promotional subsidization.

### Top 3 Recommendations

| # | Recommendation | Expected Impact | Risk |
|---|---|---|---|
| 1 | **Sunset promos for Gold tier** (no-promo buyers only) | 15–20% margin recovery on ~$42K Gold no-promo revenue | Low — these customers already buy without discounts |
| 2 | **Launch retention campaign for At-Risk segment** | Save $10–15K in at-risk revenue through targeted outreach | Medium — requires investment in CS/marketing |
| 3 | **Double down on Arizona/Kansas/Alaska** | Expand organic demand in high-opportunity states | Low — proven demand exists without promos |

---

## Part A: Promotional Sunset Plan

### Overview

The brand spends promotional budget across all customer tiers uniformly. This plan identifies which segments to gradually stop discounting, based on data evidence that they don't need promotions to buy.

### Sunset Target: Gold Tier — No-Promo Buyers

**Why this segment?**
- **507 customers** in Gold tier with `promo_dependency_score = 0` (no promo use)
- They generate **$42,098 in revenue** (64.5% of Gold tier revenue)
- Their avg loyalty score is **38.3** — solid but not the highest
- Their avg previous purchases is **15.2** — moderate engagement
- They already buy without promos — removing promos won't change behavior

**Trigger Behavior (Exact Variables):**
```
value_tier = 'Gold'
AND promo_dependency_score = 0
AND previous_purchases >= 10
AND review_rating >= 3.5
```

**Rollout Timeline:**

| Phase | Weeks | Action | Scope |
|---|---|---|---|
| **Phase 1: Pilot** | 1–4 | Stop promo codes for Gold no-promo buyers in 3 states (Arizona, Kansas, Alaska — high opportunity) | ~60 customers |
| **Phase 2: Expand** | 5–8 | If repeat rate holds (see metric below), roll out to all Gold no-promo buyers nationally | ~507 customers |
| **Phase 3: Extend** | 9–12 | Apply same logic to Silver tier no-promo buyers with prev_purchases >= 25 | ~608 customers |

**Success Metric:**
> "If repeat purchase rate within the pilot group drops more than **5 percentage points** compared to the control group (Gold buyers who keep receiving promos), pause the sunset immediately."

**Estimated Margin Impact:**
- Gold no-promo revenue at risk: **$42,098**
- If even 10% of these customers reduce spend due to no promo: **-$4,210**
- But the brand saves promo costs on remaining 90%: **+$37,888 in full-price revenue**
- Net margin improvement (at 40% COGS): **~$12,000–15,000 annually**

**Trade-off Statement:**
> **Risk:** 5–10% short-term volume dip in Gold no-promo segment during pilot phase. These customers may feel "de-prioritized."
> **Reward:** $12–15K annual margin recovery, plus clearer understanding of which customers truly need promos.
> **Mitigation:** Keep promo eligibility for Gold HIGH-promo buyers (281 customers) — they genuinely need the incentive.

---

### Secondary Sunset Candidate: Platinum Tier — Future Phase

**Why later?**
- Platinum is the highest-value tier (751 customers, $64,844 revenue)
- 48.3% already don't use promos — but the other 48.3% do
- Risk of alienating best customers is too high for initial rollout
- Wait for Phase 1–2 results before touching Platinum

**Future trigger:**
```
value_tier = 'Platinum'
AND promo_dependency_score = 0
AND previous_purchases >= 30
AND subscription_status = 'Yes'
AND review_rating >= 4.0
```

---

## Part B: Ideal Customer Profile

### Data-Backed Description

Based on top-quartile analysis (customers scoring above 63rd percentile on both loyalty_score_c and purchase_amount):

| Attribute | Value | Evidence |
|---|---|---|
| **Age Range** | 30–60 (avg 44.7) | Top quartile age distribution |
| **Gender** | Male dominant (~100%) | Dataset is male-only |
| **Avg Spend** | $70.6 per transaction | Top quartile avg purchase_amount |
| **Avg Previous Purchases** | 38.6 | 3.3x higher than bottom quartile (11.6) |
| **Avg Loyalty Score** | 67.6 | vs. 27.0 for bottom quartile |
| **Avg Review Rating** | 4.07 | Consistently high satisfaction |
| **Subscription Rate** | 45.3% | 4x higher than bottom quartile (11.6%) |
| **Promo Dependency** | 56.0% | Moderate — uses promos but doesn't depend on them |
| **Top Categories** | Clothing > Accessories > Footwear > Outerwear | Balanced portfolio |
| **Top Payment** | Credit Card, Debit Card, Cash (near-equal) | No single dominant method |
| **Top Shipping** | Store Pickup, Free Shipping, Standard | Prefers convenient/free options |
| **Satisfaction** | 60%+ Satisfied | High retention probability |

### Marketing Targeting Criteria

A marketing team should target customers matching this profile:

1. **Demographics:** Males aged 30–60
2. **Behavior:** Previous purchases ≥ 20 (proven repeat buyer)
3. **Engagement:** Subscription status = Yes OR frequency ≥ Monthly
4. **Satisfaction:** Review rating ≥ 3.5
5. **Category Interest:** Primarily Clothing + Accessories buyers
6. **Geography:** Focus on Arizona, Kansas, Alaska, Tennessee (high organic opportunity)

### What This Customer Is NOT

- ❌ NOT a discount hunter (promo dependency moderate, not extreme)
- ❌ NOT a one-time buyer (38+ previous purchases)
- ❌ NOT a low-satisfaction customer (4.07 avg rating)
- ❌ NOT a niche category buyer (spans all 4 categories)

---

## Part C: Supporting Analysis

### Revenue Concentration (Pareto)

| % of Customers | % of Revenue |
|---|---|
| Top 10% | 16.1% |
| Top 20% | 31.0% |
| Top 30% | 44.4% |
| Top 50% | 67.2% |
| Top 80% | 90.9% |
| All 100% | 100.0% |

**Interpretation:** Revenue is relatively evenly distributed — there's no extreme concentration. This means:
- Losing any single customer has moderate impact
- The brand needs broad retention, not just whale protection
- Promo ROI should be measured per-segment, not globally

### Loyalty Definition Comparison

| Metric | Score A (Frequency) | Score B (Value) | Score C (Hybrid) |
|---|---|---|---|
| Correlation with Spend | -0.01 | 0.60 | 0.34 |
| Correlation with Prev Purchases | 0.60 | 0.58 | 0.72 |
| Quartile Agreement (A vs B) | 31.9% | — | — |

**Key Insight:** Score A and Score B capture fundamentally different constructs (only 31.9% quartile agreement). Score A measures "how often" while Score B measures "how much." The hybrid (Score C) provides the most balanced view and is used for primary segmentation.

### At-Risk Customer Profile

- **680 customers** (17.4%) have satisfaction flag = "At Risk" (rating < 3.0)
- They generate **$39,786** in revenue (17.1% of total)
- Their avg loyalty score is **39.4** (moderate — not yet lost)
- Their avg previous purchases is **25.1** (they've bought before — retention is possible)
- **Top category:** Clothing
- **Top payment:** Cash

**Recommendation:** These customers are the highest-ROI retention target. They have existing purchase history but low satisfaction. A personalized outreach campaign (email + discount offer) could convert 20–30% to "Neutral" or "Satisfied," protecting $8–12K in annual revenue.

---

## Methodology Notes

### Feature Engineering Justification

Every engineered feature was built to answer a specific brand question:

| Feature | Business Question | Variables Used | Why These? |
|---|---|---|---|
| Loyalty Score A | Who comes back regularly? | Frequency, Previous Purchases, Subscription | Behavioral signals of repeat engagement |
| Loyalty Score B | Who generates revenue? | Spend, Previous Purchases, Rating | Economic value + satisfaction |
| Loyalty Score C | Balanced loyalty view | Average of A + B | Smooths frequency-vs-value extremes |
| Promo Dependency | Who needs discounts? | Discount Applied, Promo Code Used | Direct promo behavior signals |
| Value Tier | How to classify customers? | Score C + Purchase Amount (K-Means) | Data-driven, not arbitrary buckets |
| Satisfaction Flag | Who's at churn risk? | Review Rating | Only sentiment signal available |

### Data Limitations

1. **No timestamps** — Cannot measure true churn, purchase velocity, or time-between-purchases
2. **One row per customer** — Each customer appears once, so "Previous Purchases" is a cumulative count, not a trajectory
3. **No revenue decomposition** — Cannot separate product-level revenue within a customer
4. **Seasonal breadth = 1.0** — Each customer is recorded in one season only, so seasonal engagement analysis is limited

---

*Generated by the SQL-Driven Retention Strategy project.*
