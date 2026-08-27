"""
01_data_preparation.py
======================
Phase 1: Data Cleaning & Feature Engineering

Business Goal:
    Transform raw transactional data into a customer-level feature set that
    enables segmentation, loyalty analysis, and promo dependency measurement.

Outputs:
    - customer_features.csv  (enriched customer-level dataset)
    - feature_correlations.csv (correlation matrix of engineered features)

Every engineered feature is justified below with:
    1. What business question it answers
    2. Why these specific variables were chosen
    3. How it is constructed
"""

import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import MinMaxScaler
import warnings
import os

warnings.filterwarnings("ignore")

# =============================================================================
# 1. LOAD & CLEAN
# =============================================================================

def load_and_clean(path: str) -> pd.DataFrame:
    """
    Load raw CSV, handle encoding quirks, clean column names, and impute nulls.

    What it does:
        - Handles UTF-8 BOM encoding (\ufeff in first column name)
        - Strips whitespace from all string columns
        - Imputes missing Review Ratings with category-level median
        - Drops any remaining rows with critical nulls

    Business justification:
        Review Rating has ~4 missing values. Imputing with the category median
        preserves the distribution without introducing bias from global mean.
        We keep these rows because they carry full behavioral data that is
        valuable for segmentation.
    """
    df = pd.read_csv(path, encoding="utf-8-sig")

    # Clean column names (strip BOM artifacts, whitespace)
    df.columns = df.columns.str.strip().str.replace("\ufeff", "")

    # Strip whitespace from all string columns
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].str.strip()

    # Impute missing Review Rating with category-level median
    if df["Review Rating"].isnull().any():
        median_by_category = df.groupby("Category")["Review Rating"].transform("median")
        df["Review Rating"] = df["Review Rating"].fillna(median_by_category)
        # Fallback: if any category had all nulls, use global median
        df["Review Rating"] = df["Review Rating"].fillna(df["Review Rating"].median())

    # Ensure numeric types
    df["Customer ID"] = df["Customer ID"].astype(int)
    df["Age"] = df["Age"].astype(int)
    df["Purchase Amount (USD)"] = df["Purchase Amount (USD)"].astype(float)
    df["Previous Purchases"] = df["Previous Purchases"].astype(int)
    df["Review Rating"] = df["Review Rating"].astype(float)

    print(f"[CLEAN] Loaded {len(df)} customers, {len(df.columns)} columns")
    print(f"[CLEAN] Nulls remaining: {df.isnull().sum().sum()}")
    return df


# =============================================================================
# 2. FEATURE ENGINEERING
# =============================================================================

# --- 2a. Loyalty Score A (Frequency-Based) ---
# -------------------------------------------------------
# Business Question: "Who comes back regularly?"
#
# Why these variables?
#   - Frequency of Purchases: Direct behavioral signal of repeat buying.
#     Encoded ordinally (Annually=1 ... Weekly=7) to preserve ordering.
#   - Previous Purchases: Total historical purchase count — strongest
#     available proxy for customer tenure and engagement depth.
#   - Subscription Status: Binary commitment signal. Subscribers have
#     opted into ongoing engagement, which correlates with retention.
#
# Why not others?
#   - Review Rating reflects sentiment, not frequency.
#   - Purchase Amount reflects basket size, not visit regularity.
#
# Construction:
#   All three components are normalized to [0, 1] via MinMax, then
#   combined with weights: Frequency (40%), Previous Purchases (40%),
#   Subscription (20%). Final score scaled to 0–100.
# -------------------------------------------------------

FREQUENCY_MAP = {
    "Annually": 1,
    "Every 3 Months": 2,
    "Quarterly": 3,
    "Bi-Weekly": 4,
    "Fortnightly": 5,
    "Monthly": 6,
    "Weekly": 7,
}


def build_loyalty_score_a(df: pd.DataFrame) -> pd.Series:
    """
    Frequency-Based Loyalty Score (0–100).

    Captures: How often does this customer return?
    Components: Purchase frequency (40%) + Previous purchases (40%) + Subscription (20%)
    """
    scaler = MinMaxScaler()

    freq_encoded = df["Frequency of Purchases"].map(FREQUENCY_MAP).fillna(3).values.reshape(-1, 1)
    prev_purchases = df["Previous Purchases"].values.reshape(-1, 1)
    subscription = (df["Subscription Status"] == "Yes").astype(int).values.reshape(-1, 1)

    freq_norm = scaler.fit_transform(freq_encoded)
    prev_norm = scaler.fit_transform(prev_purchases)
    sub_norm = subscription  # Already 0/1

    score = 0.40 * freq_norm + 0.40 * prev_norm + 0.20 * sub_norm
    return pd.Series((score * 100).flatten(), index=df.index, name="loyalty_score_a")


# --- 2b. Loyalty Score B (Value-Based) ---
# -------------------------------------------------------
# Business Question: "Who generates sustained revenue?"
#
# Why these variables?
#   - Purchase Amount: Direct revenue contribution per transaction.
#   - Previous Purchases: High purchase count + high spend = consistently
#     valuable customer (not just one big spender).
#   - Review Rating: Satisfied customers who spend well are more likely
#     to continue — rating acts as a retention probability modifier.
#
# Why not others?
#   - Frequency is already captured in Score A (we want distinct definitions).
#   - Promo dependency is a separate axis (not value).
#
# Construction:
#   All three normalized to [0, 1], weighted equally (33% each),
#   then scaled to 0–100.
# -------------------------------------------------------

def build_loyalty_score_b(df: pd.DataFrame) -> pd.Series:
    """
    Value-Based Loyalty Score (0–100).

    Captures: How much sustained value does this customer represent?
    Components: Purchase amount (33%) + Previous purchases (33%) + Review rating (33%)
    """
    scaler = MinMaxScaler()

    purchase_amount = df["Purchase Amount (USD)"].values.reshape(-1, 1)
    prev_purchases = df["Previous Purchases"].values.reshape(-1, 1)
    review_rating = df["Review Rating"].values.reshape(-1, 1)

    amount_norm = scaler.fit_transform(purchase_amount)
    prev_norm = scaler.fit_transform(prev_purchases)
    rating_norm = scaler.fit_transform(review_rating)

    score = (1/3) * amount_norm + (1/3) * prev_norm + (1/3) * rating_norm
    return pd.Series((score * 100).flatten(), index=df.index, name="loyalty_score_b")


# --- 2c. Loyalty Score C (Hybrid Ensemble) ---
# -------------------------------------------------------
# Business Question: "What is the balanced loyalty signal?"
#
# Why a hybrid?
#   Score A captures frequency (behavioral), Score B captures value
#   (economic). A customer might score high on one but low on the other:
#     - Frequent buyer of cheap items → high A, low B
#     - Infrequent big spender → low A, high B
#   The hybrid smooths these extremes and provides a single robust metric
#   for segmentation.
#
# Construction:
#   Simple average of normalized Score A and Score B (50/50 weighting).
#   Equal weighting chosen because neither dimension is a priori more
#   important for retention strategy.
# -------------------------------------------------------

def build_loyalty_score_c(score_a: pd.Series, score_b: pd.Series) -> pd.Series:
    """
    Hybrid Ensemble Loyalty Score (0–100).

    Captures: Balanced view of frequency + value loyalty.
    Construction: Mean of normalized Score A and Score B.
    """
    scaler = MinMaxScaler()
    combined = pd.DataFrame({"a": score_a, "b": score_b})
    norm = scaler.fit_transform(combined)
    hybrid = norm.mean(axis=1)
    return pd.Series((hybrid * 100).flatten(), index=score_a.index, name="loyalty_score_c")


# --- 2d. Promo Dependency Score ---
# -------------------------------------------------------
# Business Question: "Who only buys when there's a discount?"
#
# Why these variables?
#   - Discount Applied: Binary signal — did this purchase use a discount?
#   - Promo Code Used: Independent signal — was a promo code redeemed?
#   Both together form a 0/1/2 scale measuring promo reliance depth.
#
# Why normalize against purchase frequency?
#   A customer with 1 promo use out of 50 purchases is NOT promo-dependent.
#   A customer with 1 promo use out of 2 purchases IS. Raw counts are
#   misleading; the ratio matters.
#
# Construction:
#   sum(discount_binary + promo_code_binary) / (num_purchases × 2) × 100
#   Since the dataset has one row per customer (not per purchase), we use
#   the raw flag values directly as a depth indicator.
# -------------------------------------------------------

def build_promo_dependency(df: pd.DataFrame) -> pd.Series:
    """
    Promo Dependency Score (0–100).

    Captures: How reliant is this customer on promotions?
    Construction: (discount_flag + promo_code_flag) normalized by frequency.
    """
    discount_bin = (df["Discount Applied"] == "Yes").astype(int)
    promo_bin = (df["Promo Code Used"] == "Yes").astype(int)
    raw_score = discount_bin + promo_bin  # 0, 1, or 2

    # Normalize by purchase frequency to account for volume
    freq_encoded = df["Frequency of Purchases"].map(FREQUENCY_MAP).fillna(3)
    # Higher frequency with same promo score = less dependent per-visit
    normalized = raw_score / (freq_encoded / 7)  # divide by normalized frequency
    # Cap at 2.0 and rescale to 0-100
    normalized = normalized.clip(upper=2.0)
    score = (normalized / 2.0) * 100
    return score.rename("promo_dependency_score")


# --- 2e. Value Tier ---
# -------------------------------------------------------
# Business Question: "How do we classify customers into actionable groups?"
#
# Why K-Means?
#   Data-driven clustering avoids arbitrary percentile cutoffs.
#   k=4 chosen for practical segment granularity (Platinum/Gold/Silver/Bronze)
#   — enough to differentiate, few enough to act on.
#
# Inputs: Loyalty Score C + Purchase Amount (USD)
#   These two capture the dual axes of loyalty and revenue.
#
# Why not use all features?
#   Including promo dependency or satisfaction would conflate distinct
#   dimensions. We segment on VALUE first, then analyze behavior within tiers.
# -------------------------------------------------------

def build_value_tier(df: pd.DataFrame, loyalty_c: pd.Series) -> pd.Series:
    """
    Value Tier (Platinum / Gold / Silver / Bronze).

    Captures: Actionable customer classification for targeted strategy.
    Construction: K-Means (k=4) on Loyalty Score C + Purchase Amount.
    """
    scaler = MinMaxScaler()
    features = pd.DataFrame({
        "loyalty": loyalty_c,
        "spend": df["Purchase Amount (USD)"]
    })
    features_norm = scaler.fit_transform(features)

    kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(features_norm)

    # Label clusters by centroid loyalty + spend (higher = better tier)
    centroids = kmeans.cluster_centers_
    centroid_scores = centroids.sum(axis=1)
    rank = np.argsort(centroid_scores)[::-1]  # highest first
    tier_map = {rank[0]: "Platinum", rank[1]: "Gold", rank[2]: "Silver", rank[3]: "Bronze"}

    tiers = pd.Series([tier_map[c] for c in clusters], index=df.index, name="value_tier")
    return tiers


# --- 2f. Satisfaction Flag ---
# -------------------------------------------------------
# Business Question: "Who's happy vs. at risk of churning?"
#
# Why Review Rating?
#   It's the only direct sentiment signal in the dataset. While imperfect
#   (not all satisfied customers leave reviews), it's the best available
#   proxy for customer satisfaction.
#
# Thresholds:
#   ≥ 4.0 = Satisfied (high retention probability)
#   3.0–3.9 = Neutral (retention risk — needs nurturing)
#   < 3.0 = At Risk (likely to churn without intervention)
#
# Justification: Industry standard SaaS/NPS-inspired tiers adapted for
# e-commerce rating scales (typically 1–5).
# -------------------------------------------------------

def build_satisfaction_flag(df: pd.DataFrame) -> pd.Series:
    """
    Satisfaction Flag (Satisfied / Neutral / At Risk).

    Captures: Customer sentiment and churn risk.
    Construction: Review Rating thresholds.
    """
    conditions = [
        df["Review Rating"] >= 4.0,
        df["Review Rating"] >= 3.0,
        df["Review Rating"] < 3.0,
    ]
    choices = ["Satisfied", "Neutral", "At Risk"]
    return pd.Series(np.select(conditions, choices, default="Neutral"),
                     index=df.index, name="satisfaction_flag")


# --- 2g. Category Affinity ---
# -------------------------------------------------------
# Business Question: "What product categories do high-value customers prefer?"
#
# Why?
#   Knowing that Platinum customers mostly buy Outerwear vs. Bronze buying
#   Accessories tells the brand where to focus product development and
#   cross-sell campaigns for each tier.
#
# Construction: Mode of Category per customer. (Each row = 1 purchase,
# so for single-purchase customers this is just their one category.)
# -------------------------------------------------------

def build_category_affinity(df: pd.DataFrame) -> pd.Series:
    """
    Category Affinity (most purchased category per customer).

    Captures: Product preference for targeting.
    """
    return df.groupby("Customer ID")["Category"].transform(
        lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else x.iloc[0]
    ).rename("category_affinity")


# --- 2h. Seasonal Breadth ---
# -------------------------------------------------------
# Business Question: "Is this a year-round customer or seasonal buyer?"
#
# Why?
#   Customers who buy across multiple seasons are less likely to be
#   one-time promotional buyers. Seasonal breadth correlates with
#   genuine engagement vs. opportunistic purchasing.
#
# Construction: Count of distinct seasons per customer.
# -------------------------------------------------------

def build_seasonal_breadth(df: pd.DataFrame) -> pd.Series:
    """
    Seasonal Breadth (1–4).

    Captures: How year-round is this customer's engagement?
    """
    return df.groupby("Customer ID")["Season"].transform("nunique").rename("seasonal_breadth")


# =============================================================================
# 3. CORRELATION ANALYSIS
# =============================================================================

def compute_correlations(df: pd.DataFrame, numeric_cols: list) -> pd.DataFrame:
    """
    Compute and save correlation matrix for all engineered numeric features.

    Business purpose: Validate that engineered features measure distinct
    constructs and correlate logically with each other and with revenue.
    """
    corr = df[numeric_cols].corr()
    return corr


# =============================================================================
# 4. LOYALTY DEFINITION COMPARISON
# -------------------------------------------------------
# The problem requires TWO competing loyalty definitions, tested and argued.
# Here we produce a comparison table showing how Score A vs Score B differ
# in their correlation with revenue, distribution, and segment stability.
# -------------------------------------------------------

def compare_loyalty_definitions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compare Loyalty Score A (Frequency) vs Score B (Value) on key metrics.

    Returns a DataFrame showing:
    - Correlation with Purchase Amount
    - Correlation with Previous Purchases
    - Mean and std of each score
    - Segment stability: how often do the two scores agree on top/bottom quartile?
    """
    metrics = {}

    for name, score_col in [("loyalty_score_a", "loyalty_score_a"),
                             ("loyalty_score_b", "loyalty_score_b"),
                             ("loyalty_score_c", "loyalty_score_c")]:
        s = df[score_col]
        metrics[name] = {
            "corr_with_spend": round(s.corr(df["Purchase Amount (USD)"]), 4),
            "corr_with_prev_purchases": round(s.corr(df["Previous Purchases"]), 4),
            "mean": round(s.mean(), 2),
            "std": round(s.std(), 2),
            "min": round(s.min(), 2),
            "max": round(s.max(), 2),
        }

    comparison = pd.DataFrame(metrics).T

    # Segment stability: % of customers in same quartile for A vs B
    q_a = pd.qcut(df["loyalty_score_a"], 4, labels=["Q1", "Q2", "Q3", "Q4"])
    q_b = pd.qcut(df["loyalty_score_b"], 4, labels=["Q1", "Q2", "Q3", "Q4"])
    agreement = (q_a == q_b).mean()
    comparison["quartile_agreement"] = [round(agreement, 4), "", ""]

    return comparison


# =============================================================================
# 5. MAIN PIPELINE
# =============================================================================

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(script_dir, "Dataset.csv")
    output_path = os.path.join(script_dir, "customer_features.csv")
    corr_path = os.path.join(script_dir, "feature_correlations.csv")
    comparison_path = os.path.join(script_dir, "loyalty_comparison.csv")

    print("=" * 60)
    print("PHASE 1: Data Preparation & Feature Engineering")
    print("=" * 60)

    # --- Step 1: Load & Clean ---
    print("\n--- Step 1: Loading and cleaning data ---")
    df = load_and_clean(input_path)

    # --- Step 2: Feature Engineering ---
    print("\n--- Step 2: Engineering features ---")

    # 2a. Frequency-Based Loyalty
    df["loyalty_score_a"] = build_loyalty_score_a(df)
    print(f"  [+] loyalty_score_a: mean={df['loyalty_score_a'].mean():.1f}, "
          f"std={df['loyalty_score_a'].std():.1f}")

    # 2b. Value-Based Loyalty
    df["loyalty_score_b"] = build_loyalty_score_b(df)
    print(f"  [+] loyalty_score_b: mean={df['loyalty_score_b'].mean():.1f}, "
          f"std={df['loyalty_score_b'].std():.1f}")

    # 2c. Hybrid Loyalty
    df["loyalty_score_c"] = build_loyalty_score_c(df["loyalty_score_a"], df["loyalty_score_b"])
    print(f"  [+] loyalty_score_c: mean={df['loyalty_score_c'].mean():.1f}, "
          f"std={df['loyalty_score_c'].std():.1f}")

    # 2d. Promo Dependency
    df["promo_dependency_score"] = build_promo_dependency(df)
    print(f"  [+] promo_dependency: mean={df['promo_dependency_score'].mean():.1f}, "
          f"std={df['promo_dependency_score'].std():.1f}")

    # 2e. Value Tier
    df["value_tier"] = build_value_tier(df, df["loyalty_score_c"])
    tier_counts = df["value_tier"].value_counts()
    print(f"  [+] value_tier distribution:")
    for tier in ["Platinum", "Gold", "Silver", "Bronze"]:
        if tier in tier_counts.index:
            print(f"      {tier}: {tier_counts[tier]} ({tier_counts[tier]/len(df)*100:.1f}%)")

    # 2f. Satisfaction Flag
    df["satisfaction_flag"] = build_satisfaction_flag(df)
    sat_counts = df["satisfaction_flag"].value_counts()
    print(f"  [+] satisfaction_flag distribution:")
    for flag in ["Satisfied", "Neutral", "At Risk"]:
        if flag in sat_counts.index:
            print(f"      {flag}: {sat_counts[flag]} ({sat_counts[flag]/len(df)*100:.1f}%)")

    # 2g. Category Affinity
    df["category_affinity"] = build_category_affinity(df)
    print(f"  [+] category_affinity: {df['category_affinity'].nunique()} unique categories")

    # 2h. Seasonal Breadth
    df["seasonal_breadth"] = build_seasonal_breadth(df)
    print(f"  [+] seasonal_breadth: mean={df['seasonal_breadth'].mean():.2f}")

    # --- Step 3: Correlation Analysis ---
    print("\n--- Step 3: Computing feature correlations ---")
    numeric_features = [
        "Age", "Purchase Amount (USD)", "Previous Purchases", "Review Rating",
        "loyalty_score_a", "loyalty_score_b", "loyalty_score_c",
        "promo_dependency_score", "seasonal_breadth"
    ]
    corr_matrix = compute_correlations(df, numeric_features)
    corr_matrix.to_csv(corr_path)
    print(f"  [+] Saved correlation matrix to {corr_path}")

    # --- Step 4: Loyalty Comparison ---
    print("\n--- Step 4: Comparing loyalty definitions ---")
    comparison = compare_loyalty_definitions(df)
    comparison.to_csv(comparison_path)
    print(f"  [+] Saved loyalty comparison to {comparison_path}")
    print(f"\n  Comparison table:")
    print(comparison.to_string())

    # --- Step 5: Save final dataset ---
    print(f"\n--- Step 5: Saving enriched dataset ---")
    df.to_csv(output_path, index=False)
    print(f"  [+] Saved {len(df)} customers × {len(df.columns)} features to {output_path}")

    # --- Summary ---
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Input:  {input_path}")
    print(f"  Output: {output_path}")
    print(f"  Rows:   {len(df)}")
    print(f"  Cols:   {len(df.columns)}")
    print(f"  Features added: loyalty_score_a, loyalty_score_b, loyalty_score_c,")
    print(f"                   promo_dependency_score, value_tier, satisfaction_flag,")
    print(f"                   category_affinity, seasonal_breadth")
    print("=" * 60)


if __name__ == "__main__":
    main()
