-- Вопрос: Как меняется выручка по месяцам, есть ли сезонные пики?
-- Навык: DATE_TRUNC, агрегация, группировка по времени

SELECT
    DATE_TRUNC('month', o.order_purchase_timestamp) AS month,
    SUM(oi.price)                                   AS total_revenue,
    COUNT(DISTINCT o.order_id)                      AS total_orders,
    ROUND(SUM(oi.price) / COUNT(DISTINCT o.order_id), 2) AS avg_order_value
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.order_status = 'delivered'
  AND o.order_purchase_timestamp >= '2017-01-01'
GROUP BY 1
ORDER BY 1;

-- Вопрос: Какие категории приносят больше всего денег?
-- Навык: JOIN, GROUP BY, ORDER BY, LIMIT

SELECT
    COALESCE(pct.product_category_name_english, p.product_category_name) AS category,
    SUM(oi.price)                          AS revenue,
    COUNT(DISTINCT oi.order_id)            AS orders_count,
    ROUND(AVG(oi.price), 2)                AS avg_item_price
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
LEFT JOIN product_category_translation pct
       ON p.product_category_name = pct.product_category_name
GROUP BY 1
ORDER BY revenue DESC
LIMIT 10;

-- Вопрос: Кто наши самые ценные клиенты и кто в зоне риска оттока?
-- Навык: оконные функции (NTILE), CTE

WITH rfm_base AS (
    SELECT
        c.customer_unique_id,
        MAX(o.order_purchase_timestamp)::DATE AS last_purchase_date,
        COUNT(DISTINCT o.order_id)            AS frequency,
        SUM(oi.price)                         AS monetary
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id
),
rfm_scores AS (
    SELECT
        customer_unique_id,
        last_purchase_date,
        frequency,
        monetary,
        -- Recency: чем меньше дней с последней покупки, тем выше балл
        NTILE(4) OVER (ORDER BY last_purchase_date DESC) AS r_score,
        NTILE(4) OVER (ORDER BY frequency ASC)          AS f_score,
        NTILE(4) OVER (ORDER BY monetary ASC)           AS m_score
    FROM rfm_base
)
SELECT
    CASE
        WHEN r_score >= 3 AND f_score >= 3 AND m_score >= 3 THEN 'Champions'
        WHEN r_score >= 3 AND f_score >= 3                  THEN 'Loyal'
        WHEN r_score <= 2 AND f_score >= 3 AND m_score >= 3 THEN 'At Risk'
        WHEN r_score <= 2 AND f_score <= 2                  THEN 'Hibernating'
        ELSE 'Others'
    END                AS segment,
    COUNT(*)           AS customers,
    ROUND(AVG(monetary), 2) AS avg_monetary,
    ROUND(AVG(frequency), 1) AS avg_frequency
FROM rfm_scores
GROUP BY 1
ORDER BY customers DESC;

-- Вопрос: Правда ли, что опоздавшие заказы получают более низкие оценки?
-- Навык: расчёт разницы дат, CASE, AVG

SELECT
    CASE
        WHEN o.order_delivered_customer_date <= o.order_estimated_delivery_date
            THEN 'On time'
        ELSE 'Late'
    END                          AS delivery_status,
    COUNT(DISTINCT o.order_id)   AS orders_count,
    ROUND(AVG(r.review_score), 2) AS avg_review_score
FROM orders o
JOIN order_reviews r ON o.order_id = r.order_id
WHERE o.order_status = 'delivered'
  AND o.order_delivered_customer_date IS NOT NULL
GROUP BY 1;

-- Вопрос: Какой процент клиентов возвращается после первой покупки?
-- Навык: self-join, date-math CTE

WITH first_purchase AS (
    SELECT
        c.customer_unique_id,
        MIN(DATE_TRUNC('month', o.order_purchase_timestamp)) AS cohort_month
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id
),
orders_with_cohort AS (
    SELECT
        c.customer_unique_id,
        fp.cohort_month,
        DATE_TRUNC('month', o.order_purchase_timestamp) AS order_month
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    JOIN first_purchase fp ON c.customer_unique_id = fp.customer_unique_id
    WHERE o.order_status = 'delivered'
)
SELECT
    cohort_month,
    order_month,
    EXTRACT(MONTH FROM AGE(order_month, cohort_month)) AS month_number,
    COUNT(DISTINCT customer_unique_id)                  AS active_customers
FROM orders_with_cohort
GROUP BY 1, 2, 3
ORDER BY 1, 3;

-- Вопрос: На каком этапе теряется больше всего заказов?
-- Навык: условная агрегация, расчёт конверсии

WITH funnel AS (
    SELECT
        COUNT(*)                                                         AS created,
        COUNT(CASE WHEN order_approved_at IS NOT NULL THEN 1 END)        AS approved,
        COUNT(CASE WHEN order_delivered_carrier_date IS NOT NULL THEN 1 END) AS shipped,
        COUNT(CASE WHEN order_delivered_customer_date IS NOT NULL THEN 1 END) AS delivered
    FROM orders
)
SELECT
    created,
    approved,
    shipped,
    delivered,
    ROUND(approved  * 100.0 / created, 1)  AS approval_rate_pct,
    ROUND(shipped   * 100.0 / approved, 1) AS ship_rate_pct,
    ROUND(delivered * 100.0 / shipped, 1)  AS delivery_rate_pct
FROM funnel;
