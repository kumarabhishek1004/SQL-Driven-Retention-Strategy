"""
03_generate_dashboard_data.py
=============================
Phase 3: Export Dashboard Data

Runs analytical queries against customer_intel.db and exports structured
JSON for the four-panel interactive dashboard.

Panels:
  1. Customer Pyramid (value tier distribution + revenue)
  2. Promo Dependency vs Retention (scatter data)
  3. Geographic Opportunity Map (state-level metrics)
  4. Category Funnel (category × retention metrics)
"""

import sqlite3
import json
import os

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "customer_intel.db")
OUTPUT_DIR = os.path.join(DB_DIR, "03_dashboard")
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "dashboard_data.json")


def query_all(conn, sql):
    """Execute query and return list of dicts."""
    cur = conn.execute(sql)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def build_dashboard_data(conn):
    """Build all four panels + summary stats."""

    # ── Panel 1: Customer Pyramid ──
    pyramid = query_all(conn, """
        SELECT
            value_tier AS tier,
            COUNT(*) AS customer_count,
            ROUND(SUM(CAST(purchase_amount_usd AS REAL)), 0) AS total_revenue,
            ROUND(AVG(CAST(purchase_amount_usd AS REAL)), 1) AS avg_spend,
            ROUND(AVG(CAST(loyalty_score_c AS REAL)), 1) AS avg_loyalty,
            ROUND(AVG(CAST(review_rating AS REAL)), 2) AS avg_rating
        FROM customers
        GROUP BY value_tier
        ORDER BY
            CASE value_tier WHEN 'Platinum' THEN 1 WHEN 'Gold' THEN 2
                 WHEN 'Silver' THEN 3 ELSE 4 END
    """)

    total_rev = sum(r["total_revenue"] for r in pyramid)
    for r in pyramid:
        r["revenue_pct"] = round(r["total_revenue"] / total_rev * 100, 1) if total_rev else 0

    # ── Panel 2: Promo Dependency vs Retention (scatter) ──
    scatter = query_all(conn, """
        SELECT
            customer_id,
            CAST(promo_dependency_score AS REAL) AS promo_dep,
            CAST(loyalty_score_c AS REAL) AS loyalty,
            CAST(purchase_amount_usd AS REAL) AS spend,
            value_tier AS tier,
            CAST(previous_purchases AS INTEGER) AS prev_purchases,
            satisfaction_flag AS satisfaction
        FROM customers
        ORDER BY customer_id
    """)

    # ── Panel 3: Geographic Opportunity Map ──
    geo = query_all(conn, """
        SELECT
            location AS state,
            COUNT(*) AS customer_count,
            ROUND(AVG(CAST(purchase_amount_usd AS REAL)), 1) AS avg_spend,
            ROUND(SUM(CAST(purchase_amount_usd AS REAL)), 0) AS total_revenue,
            ROUND(AVG(CAST(promo_dependency_score AS REAL)), 1) AS avg_promo_dep,
            ROUND(AVG(CAST(loyalty_score_c AS REAL)), 1) AS avg_loyalty,
            ROUND(
                (AVG(CAST(purchase_amount_usd AS REAL)) / 100.0) *
                (1.0 - AVG(CAST(promo_dependency_score AS REAL)) / 100.0) * 100,
                1
            ) AS organic_opportunity_score
        FROM customers
        GROUP BY location
        ORDER BY organic_opportunity_score DESC
    """)

    # ── Panel 4: Category Funnel ──
    category_funnel = query_all(conn, """
        SELECT
            category,
            COUNT(*) AS customer_count,
            ROUND(AVG(CAST(purchase_amount_usd AS REAL)), 1) AS avg_spend,
            ROUND(AVG(CAST(previous_purchases AS REAL)), 1) AS avg_prev_purchases,
            ROUND(AVG(CAST(loyalty_score_c AS REAL)), 1) AS avg_loyalty,
            ROUND(AVG(CAST(review_rating AS REAL)), 2) AS avg_rating,
            ROUND(SUM(CAST(purchase_amount_usd AS REAL)), 0) AS total_revenue
        FROM customers
        GROUP BY category
        ORDER BY avg_prev_purchases DESC
    """)

    # ── Bonus: Value Tier × Promo Level (for playbook) ──
    tier_promo = query_all(conn, """
        SELECT
            value_tier,
            CASE
                WHEN CAST(promo_dependency_score AS REAL) >= 50 THEN 'High Promo Use'
                WHEN CAST(promo_dependency_score AS REAL) > 0 THEN 'Some Promo Use'
                ELSE 'No Promo'
            END AS promo_level,
            COUNT(*) AS customer_count,
            ROUND(SUM(CAST(purchase_amount_usd AS REAL)), 0) AS total_revenue,
            ROUND(AVG(CAST(loyalty_score_c AS REAL)), 1) AS avg_loyalty,
            ROUND(AVG(CAST(previous_purchases AS REAL)), 1) AS avg_prev_purchases
        FROM customers
        GROUP BY value_tier, promo_level
        ORDER BY
            CASE value_tier WHEN 'Platinum' THEN 1 WHEN 'Gold' THEN 2 WHEN 'Silver' THEN 3 ELSE 4 END,
            CASE promo_level WHEN 'No Promo' THEN 1 WHEN 'Some Promo Use' THEN 2 ELSE 3 END
    """)

    # ── Summary Stats ──
    summary = query_all(conn, """
        SELECT
            COUNT(*) AS total_customers,
            ROUND(SUM(CAST(purchase_amount_usd AS REAL)), 0) AS total_revenue,
            ROUND(AVG(CAST(purchase_amount_usd AS REAL)), 1) AS avg_spend,
            ROUND(AVG(CAST(review_rating AS REAL)), 2) AS avg_rating,
            ROUND(AVG(CAST(previous_purchases AS REAL)), 1) AS avg_prev_purchases,
            ROUND(AVG(CAST(loyalty_score_c AS REAL)), 1) AS avg_loyalty,
            ROUND(AVG(CAST(promo_dependency_score AS REAL)), 1) AS avg_promo_dep,
            ROUND(AVG(CASE WHEN subscription_status = 'Yes' THEN 1.0 ELSE 0.0 END) * 100, 1) AS pct_subscribed
        FROM customers
    """)[0]

    # ── Loyalty Segment Stats ──
    loyalty_segments = query_all(conn, """
        SELECT
            CASE
                WHEN CAST(loyalty_score_c AS REAL) >= 47.2
                     AND CAST(promo_dependency_score AS REAL) < 43.0
                THEN 'Organic Loyal'
                WHEN CAST(loyalty_score_c AS REAL) >= 47.2
                     AND CAST(promo_dependency_score AS REAL) >= 43.0
                THEN 'Loyal but Promo-Sensitive'
                WHEN CAST(loyalty_score_c AS REAL) < 47.2
                     AND CAST(promo_dependency_score AS REAL) < 43.0
                THEN 'Occasional Buyer'
                ELSE 'Discount-Dependent'
            END AS loyalty_segment,
            COUNT(*) AS customer_count,
            ROUND(SUM(CAST(purchase_amount_usd AS REAL)), 0) AS total_revenue,
            ROUND(AVG(CAST(loyalty_score_c AS REAL)), 1) AS avg_loyalty,
            ROUND(AVG(CAST(promo_dependency_score AS REAL)), 1) AS avg_promo_dep
        FROM customers
        GROUP BY loyalty_segment
        ORDER BY avg_loyalty DESC
    """)

    return {
        "pyramid": pyramid,
        "scatter": scatter,
        "geo": geo,
        "category_funnel": category_funnel,
        "tier_promo": tier_promo,
        "summary": summary,
        "loyalty_segments": loyalty_segments,
    }


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=" * 60)
    print("PHASE 3: Generating Dashboard Data")
    print("=" * 60)

    conn = sqlite3.connect(DB_PATH)
    data = build_dashboard_data(conn)
    conn.close()

    with open(OUTPUT_PATH, "w") as f:
        json.dump(data, f, indent=2, default=str)

    print(f"\n[OK] Dashboard data exported to: {OUTPUT_PATH}")
    print(f"     Panels: pyramid({len(data['pyramid'])}), "
          f"scatter({len(data['scatter'])}), "
          f"geo({len(data['geo'])}), "
          f"category_funnel({len(data['category_funnel'])})")
    print(f"     Summary: {data['summary']['total_customers']} customers, "
          f"${data['summary']['total_revenue']:,.0f} total revenue")


if __name__ == "__main__":
    main()
