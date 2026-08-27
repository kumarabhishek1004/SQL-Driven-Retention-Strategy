-- ============================================================================
-- 02_segmentation.sql
-- ============================================================================
-- SQL Segmentation Queries for: Decoding Customer Value
--
-- Business Goal:
--   Answer 5 core questions about customer loyalty, promo dependency,
--   geographic opportunity, category performance, and ideal customer profile.
--
-- Database: SQLite (customer_intel.db)
-- Table: customers (3,900 rows, 26 columns)
-- ============================================================================


-- ============================================================================
-- Q1: LOYAL vs. DISCOUNT-ONLY CUSTOMERS
-- ============================================================================
-- Key Question: "Who are the genuinely loyal customers vs. those who only
-- buy when there is a discount?"
--
-- Approach:
--   Segment customers into 4 groups using loyalty_score_c (hybrid) and
--   promo_dependency_score. This creates a 2x2 matrix:
--     - High Loyalty + Low Promo = "Organic Loyal"
--     - High Loyalty + High Promo = "Loyal but Promo-Sensitive"
--     - Low Loyalty + Low Promo = "Occasional Buyer"
--     - Low Loyalty + High Promo = "Discount-Dependent"
--
-- Metrics per segment: count, avg spend, avg rating, avg previous purchases,
-- avg loyalty, revenue contribution (%)
-- ============================================================================

-- QUERY: Q1 — Customer Loyalty vs Promo Dependency Segments

WITH loyalty_promo_matrix AS (
    SELECT
        *,
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
        END AS loyalty_segment
    FROM customers
)
SELECT
    loyalty_segment,
    COUNT(*) AS customer_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM customers), 1) AS pct_of_customers,
    ROUND(AVG(CAST(purchase_amount_usd AS REAL)), 1) AS avg_spend,
    ROUND(AVG(CAST(review_rating AS REAL)), 2) AS avg_rating,
    ROUND(AVG(CAST(previous_purchases AS REAL)), 1) AS avg_prev_purchases,
    ROUND(AVG(CAST(loyalty_score_c AS REAL)), 1) AS avg_loyalty,
    ROUND(AVG(CAST(promo_dependency_score AS REAL)), 1) AS avg_promo_dep,
    ROUND(SUM(CAST(purchase_amount_usd AS REAL)), 0) AS total_revenue,
    ROUND(SUM(CAST(purchase_amount_usd AS REAL)) * 100.0 /
          (SELECT SUM(CAST(purchase_amount_usd AS REAL)) FROM customers), 1) AS revenue_pct
FROM loyalty_promo_matrix
GROUP BY loyalty_segment
ORDER BY avg_loyalty DESC;


-- ============================================================================
-- Q2: BEHAVIORAL PATTERNS PREDICTING HIGH VALUE
-- ============================================================================
-- Key Question: "What behavioral patterns today predict high customer value
-- over time?"
--
-- Approach:
--   Compare top quartile (loyalty_score_c >= 63.0) vs bottom quartile
--   on all behavioral dimensions. The DIFFERENCE between these groups
--   reveals which signals predict value.
-- ============================================================================

-- QUERY: Q2 — High-Value vs Low-Value Customer Profiles

WITH ranked AS (
    SELECT
        *,
        NTILE(4) OVER (ORDER BY CAST(loyalty_score_c AS REAL)) AS loyalty_quartile
    FROM customers
),
quartile_comparison AS (
    SELECT
        CASE WHEN loyalty_quartile = 4 THEN 'Top Quartile (High Value)'
             WHEN loyalty_quartile = 1 THEN 'Bottom Quartile (Low Value)'
             ELSE 'Middle' END AS segment,
        COUNT(*) AS count,
        ROUND(AVG(CAST(age AS REAL)), 1) AS avg_age,
        ROUND(AVG(CAST(purchase_amount_usd AS REAL)), 1) AS avg_spend,
        ROUND(AVG(CAST(previous_purchases AS REAL)), 1) AS avg_prev_purchases,
        ROUND(AVG(CAST(review_rating AS REAL)), 2) AS avg_rating,
        ROUND(AVG(CAST(loyalty_score_c AS REAL)), 1) AS avg_loyalty,
        ROUND(AVG(CAST(promo_dependency_score AS REAL)), 1) AS avg_promo_dep,
        ROUND(AVG(CASE WHEN subscription_status = 'Yes' THEN 1.0 ELSE 0.0 END) * 100, 1) AS pct_subscribed,
        ROUND(AVG(CASE WHEN discount_applied = 'Yes' THEN 1.0 ELSE 0.0 END) * 100, 1) AS pct_discount,
        ROUND(AVG(CAST(seasonal_breadth AS REAL)), 2) AS avg_seasons
    FROM ranked
    WHERE loyalty_quartile IN (1, 4)
    GROUP BY segment
)
SELECT * FROM quartile_comparison
ORDER BY avg_loyalty DESC;


-- ============================================================================
-- Q3: UNDERLEVERED GEOGRAPHIES
-- ============================================================================
-- Key Question: "Which cities or regions where the brand has strong traction
-- that it has not yet deliberately targeted?"
--
-- Approach:
--   GROUP BY location and rank states by:
--     1. Avg spend (high = strong traction)
--     2. Avg promo dependency (low = organic demand, not discount-driven)
--   States with high spend + LOW promo dependency = genuine brand pull.
-- ============================================================================

-- QUERY: Q3 — Geographic Opportunity Analysis (Top 20 States)

SELECT
    location AS state,
    COUNT(*) AS customer_count,
    ROUND(AVG(CAST(purchase_amount_usd AS REAL)), 1) AS avg_spend,
    ROUND(SUM(CAST(purchase_amount_usd AS REAL)), 0) AS total_revenue,
    ROUND(AVG(CAST(promo_dependency_score AS REAL)), 1) AS avg_promo_dep,
    ROUND(AVG(CAST(loyalty_score_c AS REAL)), 1) AS avg_loyalty,
    ROUND(AVG(CAST(review_rating AS REAL)), 2) AS avg_rating,
    -- Opportunity score: high spend + low promo = high organic pull
    ROUND(
        (AVG(CAST(purchase_amount_usd AS REAL)) / 100.0) *
        (1.0 - AVG(CAST(promo_dependency_score AS REAL)) / 100.0) * 100,
        1
    ) AS organic_opportunity_score,
    -- Most common category
    (
        SELECT category FROM customers c2
        WHERE c2.location = customers.location
        GROUP BY category ORDER BY COUNT(*) DESC LIMIT 1
    ) AS top_category,
    -- Most common payment method
    (
        SELECT payment_method FROM customers c3
        WHERE c3.location = customers.location
        GROUP BY payment_method ORDER BY COUNT(*) DESC LIMIT 1
    ) AS top_payment
FROM customers
GROUP BY location
ORDER BY organic_opportunity_score DESC
LIMIT 20;


-- ============================================================================
-- Q4: PROMO RESTRUCTURING — Revenue Impact Analysis
-- ============================================================================
-- Key Question: "How should the brand restructure its promotional strategy
-- to protect margins without losing volume?"
--
-- Approach:
--   Cross-tabulate value_tier × promo_dependency to show:
--     - Which tiers buy mostly with/without discounts
--     - Revenue at risk if discounts are removed
--     - Estimated margin improvement (assume 40% COGS)
-- ============================================================================

-- QUERY: Q4 — Promo Impact by Value Tier

WITH tier_promo AS (
    SELECT
        value_tier,
        CASE
            WHEN CAST(promo_dependency_score AS REAL) >= 50 THEN 'High Promo Use'
            WHEN CAST(promo_dependency_score AS REAL) > 0 THEN 'Some Promo Use'
            ELSE 'No Promo'
        END AS promo_level,
        COUNT(*) AS customer_count,
        ROUND(AVG(CAST(purchase_amount_usd AS REAL)), 1) AS avg_spend,
        SUM(CAST(purchase_amount_usd AS REAL)) AS total_revenue,
        ROUND(AVG(CAST(loyalty_score_c AS REAL)), 1) AS avg_loyalty,
        ROUND(AVG(CAST(review_rating AS REAL)), 2) AS avg_rating,
        ROUND(AVG(CAST(previous_purchases AS REAL)), 1) AS avg_prev_purchases
    FROM customers
    GROUP BY value_tier, promo_level
)
SELECT
    value_tier,
    promo_level,
    customer_count,
    avg_spend,
    ROUND(total_revenue, 0) AS total_revenue,
    ROUND(total_revenue * 0.4, 0) AS estimated_margin_40pct_cogs,
    avg_loyalty,
    avg_rating,
    avg_prev_purchases,
    ROUND(total_revenue * 100.0 /
          SUM(total_revenue) OVER (PARTITION BY value_tier), 1) AS pct_of_tier_revenue
FROM tier_promo
ORDER BY
    CASE value_tier WHEN 'Platinum' THEN 1 WHEN 'Gold' THEN 2 WHEN 'Silver' THEN 3 ELSE 4 END,
    CASE promo_level WHEN 'No Promo' THEN 1 WHEN 'Some Promo Use' THEN 2 ELSE 3 END;


-- ============================================================================
-- Q5: IDEAL CUSTOMER PROFILE
-- ============================================================================
-- Key Question: "What does the brand's ideal customer actually look like?"
--
-- Approach:
--   Profile the top quartile by loyalty_score_c + purchase_amount_usd.
--   Show demographic, behavioral, and transactional characteristics
--   specific enough for marketing targeting.
-- ============================================================================

-- QUERY: Q5a — Ideal Customer Profile (Top Quartile Summary)

WITH top_customers AS (
    SELECT *
    FROM customers
    WHERE CAST(loyalty_score_c AS REAL) >= (
        SELECT CAST(loyalty_score_c AS REAL) FROM customers
        ORDER BY CAST(loyalty_score_c AS REAL) DESC
        LIMIT 1 OFFSET (SELECT COUNT(*) / 4 FROM customers)
    )
    AND CAST(purchase_amount_usd AS REAL) >= (
        SELECT CAST(purchase_amount_usd AS REAL) FROM customers
        ORDER BY CAST(purchase_amount_usd AS REAL) DESC
        LIMIT 1 OFFSET (SELECT COUNT(*) / 4 FROM customers)
    )
)
SELECT
    COUNT(*) AS profile_size,
    ROUND(AVG(CAST(age AS REAL)), 1) AS avg_age,
    MIN(CAST(age AS INTEGER)) AS min_age,
    MAX(CAST(age AS INTEGER)) AS max_age,
    ROUND(AVG(CASE WHEN gender = 'Male' THEN 1.0 ELSE 0.0 END) * 100, 1) AS pct_male,
    ROUND(AVG(CAST(purchase_amount_usd AS REAL)), 1) AS avg_spend,
    ROUND(AVG(CAST(previous_purchases AS REAL)), 1) AS avg_prev_purchases,
    ROUND(AVG(CAST(loyalty_score_c AS REAL)), 1) AS avg_loyalty_score,
    ROUND(AVG(CAST(promo_dependency_score AS REAL)), 1) AS avg_promo_dep,
    ROUND(AVG(CAST(review_rating AS REAL)), 2) AS avg_rating,
    ROUND(AVG(CASE WHEN subscription_status = 'Yes' THEN 1.0 ELSE 0.0 END) * 100, 1) AS pct_subscribed
FROM top_customers;


-- QUERY: Q5b — Ideal Customer: Top Categories

WITH top_customers AS (
    SELECT *
    FROM customers
    WHERE CAST(loyalty_score_c AS REAL) >= (
        SELECT CAST(loyalty_score_c AS REAL) FROM customers
        ORDER BY CAST(loyalty_score_c AS REAL) DESC
        LIMIT 1 OFFSET (SELECT COUNT(*) / 4 FROM customers)
    )
    AND CAST(purchase_amount_usd AS REAL) >= (
        SELECT CAST(purchase_amount_usd AS REAL) FROM customers
        ORDER BY CAST(purchase_amount_usd AS REAL) DESC
        LIMIT 1 OFFSET (SELECT COUNT(*) / 4 FROM customers)
    )
)
SELECT category, COUNT(*) AS customer_count,
       ROUND(AVG(CAST(purchase_amount_usd AS REAL)), 1) AS avg_spend
FROM top_customers
GROUP BY category ORDER BY customer_count DESC;


-- QUERY: Q5c — Ideal Customer: Top Payment Methods

WITH top_customers AS (
    SELECT *
    FROM customers
    WHERE CAST(loyalty_score_c AS REAL) >= (
        SELECT CAST(loyalty_score_c AS REAL) FROM customers
        ORDER BY CAST(loyalty_score_c AS REAL) DESC
        LIMIT 1 OFFSET (SELECT COUNT(*) / 4 FROM customers)
    )
    AND CAST(purchase_amount_usd AS REAL) >= (
        SELECT CAST(purchase_amount_usd AS REAL) FROM customers
        ORDER BY CAST(purchase_amount_usd AS REAL) DESC
        LIMIT 1 OFFSET (SELECT COUNT(*) / 4 FROM customers)
    )
)
SELECT payment_method, COUNT(*) AS customer_count
FROM top_customers
GROUP BY payment_method ORDER BY customer_count DESC;


-- QUERY: Q5d — Ideal Customer: Top Shipping Types

WITH top_customers AS (
    SELECT *
    FROM customers
    WHERE CAST(loyalty_score_c AS REAL) >= (
        SELECT CAST(loyalty_score_c AS REAL) FROM customers
        ORDER BY CAST(loyalty_score_c AS REAL) DESC
        LIMIT 1 OFFSET (SELECT COUNT(*) / 4 FROM customers)
    )
    AND CAST(purchase_amount_usd AS REAL) >= (
        SELECT CAST(purchase_amount_usd AS REAL) FROM customers
        ORDER BY CAST(purchase_amount_usd AS REAL) DESC
        LIMIT 1 OFFSET (SELECT COUNT(*) / 4 FROM customers)
    )
)
SELECT shipping_type, COUNT(*) AS customer_count
FROM top_customers
GROUP BY shipping_type ORDER BY customer_count DESC;


-- QUERY: Q5e — Ideal Customer: Satisfaction Breakdown

WITH top_customers AS (
    SELECT *
    FROM customers
    WHERE CAST(loyalty_score_c AS REAL) >= (
        SELECT CAST(loyalty_score_c AS REAL) FROM customers
        ORDER BY CAST(loyalty_score_c AS REAL) DESC
        LIMIT 1 OFFSET (SELECT COUNT(*) / 4 FROM customers)
    )
    AND CAST(purchase_amount_usd AS REAL) >= (
        SELECT CAST(purchase_amount_usd AS REAL) FROM customers
        ORDER BY CAST(purchase_amount_usd AS REAL) DESC
        LIMIT 1 OFFSET (SELECT COUNT(*) / 4 FROM customers)
    )
)
SELECT satisfaction_flag, COUNT(*) AS customer_count
FROM top_customers
GROUP BY satisfaction_flag ORDER BY customer_count DESC;


-- ============================================================================
-- ADDITIONAL ANALYSIS: PARETO (Revenue Concentration)
-- ============================================================================
-- What % of revenue comes from top 10%, 20%, 50% of customers?

-- QUERY: Pareto Revenue Concentration

WITH ranked_revenue AS (
    SELECT
        customer_id,
        CAST(purchase_amount_usd AS REAL) AS spend,
        SUM(CAST(purchase_amount_usd AS REAL)) OVER () AS total_revenue,
        ROW_NUMBER() OVER (ORDER BY CAST(purchase_amount_usd AS REAL) DESC) AS rn,
        COUNT(*) OVER () AS total_customers
    FROM customers
),
cumulative AS (
    SELECT
        rn,
        total_customers,
        spend,
        total_revenue,
        SUM(spend) OVER (ORDER BY rn) AS cumulative_spend,
        ROUND(rn * 100.0 / total_customers, 1) AS customer_pct
    FROM ranked_revenue
)
SELECT DISTINCT
    customer_pct,
    ROUND(cumulative_spend * 100.0 / total_revenue, 1) AS revenue_pct
FROM cumulative
WHERE customer_pct IN (10, 20, 30, 40, 50, 60, 70, 80, 90, 100)
ORDER BY customer_pct;


-- ============================================================================
-- ADDITIONAL ANALYSIS: CATEGORY × VALUE TIER CROSS-TAB
-- ============================================================================

-- QUERY: Category Performance by Value Tier

SELECT
    value_tier,
    category,
    COUNT(*) AS customer_count,
    ROUND(AVG(CAST(purchase_amount_usd AS REAL)), 1) AS avg_spend,
    ROUND(AVG(CAST(loyalty_score_c AS REAL)), 1) AS avg_loyalty,
    ROUND(AVG(CAST(review_rating AS REAL)), 2) AS avg_rating,
    ROUND(AVG(CAST(previous_purchases AS REAL)), 1) AS avg_prev_purchases,
    ROUND(SUM(CAST(purchase_amount_usd AS REAL)), 0) AS total_revenue
FROM customers
GROUP BY value_tier, category
ORDER BY
    CASE value_tier WHEN 'Platinum' THEN 1 WHEN 'Gold' THEN 2 WHEN 'Silver' THEN 3 ELSE 4 END,
    total_revenue DESC;


-- ============================================================================
-- ADDITIONAL ANALYSIS: SEASON × TENURE (Previous Purchases)
-- ============================================================================

-- QUERY: Seasonal Engagement by Customer Tenure

SELECT
    season,
    CASE
        WHEN CAST(previous_purchases AS INTEGER) >= 40 THEN 'High Tenure (40+)'
        WHEN CAST(previous_purchases AS INTEGER) >= 20 THEN 'Medium Tenure (20-39)'
        ELSE 'Low Tenure (<20)'
    END AS tenure_group,
    COUNT(*) AS customer_count,
    ROUND(AVG(CAST(purchase_amount_usd AS REAL)), 1) AS avg_spend,
    ROUND(AVG(CAST(loyalty_score_c AS REAL)), 1) AS avg_loyalty,
    ROUND(AVG(CAST(promo_dependency_score AS REAL)), 1) AS avg_promo_dep,
    ROUND(AVG(CAST(review_rating AS REAL)), 2) AS avg_rating
FROM customers
GROUP BY season, tenure_group
ORDER BY season,
    CASE tenure_group
        WHEN 'High Tenure (40+)' THEN 1
        WHEN 'Medium Tenure (20-39)' THEN 2
        ELSE 3
    END;


-- ============================================================================
-- ADDITIONAL ANALYSIS: LOYALTY DEFINITION COMPARISON (A vs B vs C)
-- ============================================================================

-- QUERY: Loyalty Score Comparison — Segment Overlap

WITH score_segments AS (
    SELECT
        customer_id,
        loyalty_score_a,
        loyalty_score_b,
        loyalty_score_c,
        CASE WHEN CAST(loyalty_score_a AS REAL) >= 45 THEN 'High' ELSE 'Low' END AS seg_a,
        CASE WHEN CAST(loyalty_score_b AS REAL) >= 50 THEN 'High' ELSE 'Low' END AS seg_b,
        CASE WHEN CAST(loyalty_score_c AS REAL) >= 47 THEN 'High' ELSE 'Low' END AS seg_c
    FROM customers
)
SELECT
    seg_a,
    seg_b,
    seg_c,
    COUNT(*) AS customer_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM customers), 1) AS pct,
    ROUND(AVG(CAST(purchase_amount_usd AS REAL)), 1) AS avg_spend,
    ROUND(AVG(CAST(previous_purchases AS REAL)), 1) AS avg_prev_purchases
FROM score_segments
JOIN customers USING (customer_id)
GROUP BY seg_a, seg_b, seg_c
ORDER BY seg_a DESC, seg_b DESC, seg_c DESC;


-- ============================================================================
-- ADDITIONAL ANALYSIS: PAYMENT METHOD × VALUE TIER
-- ============================================================================

-- QUERY: Payment Preferences by Value Tier

SELECT
    value_tier,
    payment_method,
    COUNT(*) AS customer_count,
    ROUND(AVG(CAST(purchase_amount_usd AS REAL)), 1) AS avg_spend,
    ROUND(AVG(CAST(loyalty_score_c AS REAL)), 1) AS avg_loyalty,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY value_tier), 1) AS pct_of_tier
FROM customers
GROUP BY value_tier, payment_method
ORDER BY
    CASE value_tier WHEN 'Platinum' THEN 1 WHEN 'Gold' THEN 2 WHEN 'Silver' THEN 3 ELSE 4 END,
    customer_count DESC;


-- ============================================================================
-- ADDITIONAL ANALYSIS: AT-RISK CUSTOMERS (Satisfaction = "At Risk")
-- ============================================================================

-- QUERY: At-Risk Customer Profile

SELECT
    satisfaction_flag,
    COUNT(*) AS customer_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM customers), 1) AS pct_of_total,
    ROUND(AVG(CAST(purchase_amount_usd AS REAL)), 1) AS avg_spend,
    ROUND(AVG(CAST(previous_purchases AS REAL)), 1) AS avg_prev_purchases,
    ROUND(AVG(CAST(loyalty_score_c AS REAL)), 1) AS avg_loyalty,
    ROUND(AVG(CAST(promo_dependency_score AS REAL)), 1) AS avg_promo_dep,
    ROUND(AVG(CAST(review_rating AS REAL)), 2) AS avg_rating,
    ROUND(SUM(CAST(purchase_amount_usd AS REAL)), 0) AS total_revenue,
    -- Most common categories
    (
        SELECT category FROM customers c2
        WHERE c2.satisfaction_flag = customers.satisfaction_flag
        GROUP BY category ORDER BY COUNT(*) DESC LIMIT 1
    ) AS top_category,
    -- Most common payment
    (
        SELECT payment_method FROM customers c3
        WHERE c3.satisfaction_flag = customers.satisfaction_flag
        GROUP BY payment_method ORDER BY COUNT(*) DESC LIMIT 1
    ) AS top_payment
FROM customers
GROUP BY satisfaction_flag
ORDER BY avg_loyalty;
