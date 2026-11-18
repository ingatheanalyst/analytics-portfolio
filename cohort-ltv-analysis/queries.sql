1. Когортный анализ Retention (Удержание)

WITH UserCohorts AS (
    -- Определяем месяц регистрации (когорту) для каждого пользователя
    SELECT 
        user_id,
        STRFTIME('%Y-%m', reg_date) AS cohort_month
    FROM users
),
OrderMonths AS (
    -- Определяем месяц покупки и связываем с когортой через JOIN
    SELECT 
        o.user_id,
        uc.cohort_month, -- Берем из CTE UserCohorts
        -- Считаем разницу в месяцах между покупкой и регистрацией
        (CAST(STRFTIME('%Y', o.order_date) AS INTEGER) - CAST(STRFTIME('%Y', u.reg_date) AS INTEGER)) * 12 + 
        (CAST(STRFTIME('%m', o.order_date) AS INTEGER) - CAST(STRFTIME('%m', u.reg_date) AS INTEGER)) AS month_diff
    FROM orders o
    JOIN users u ON o.user_id = u.user_id
    JOIN UserCohorts uc ON o.user_id = uc.user_id -- Связываем с когортой
)
SELECT 
    cohort_month,
    month_diff,
    COUNT(DISTINCT user_id) AS active_users
FROM OrderMonths
GROUP BY cohort_month, month_diff
ORDER BY cohort_month, month_diff;

2. LTV (Lifetime Value) по каналам
Считает, сколько в среднем приносит пользователь из конкретного канала за все время.

SELECT 
    u.channel,
    ROUND(SUM(o.amount) * 1.0 / COUNT(DISTINCT u.user_id), 2) AS ltv
FROM users u
LEFT JOIN orders o ON u.user_id = o.user_id
GROUP BY u.channel
ORDER BY ltv DESC;


3. Окупаемость маркетинга (CAC vs LTV)
Сравнивает затраты на привлечение с доходом по каналам.

WITH ChannelLTV AS (
    SELECT u.channel, SUM(o.amount) AS total_revenue, COUNT(DISTINCT u.user_id) AS total_users,
           ROUND(SUM(o.amount) * 1.0 / COUNT(DISTINCT u.user_id), 2) AS ltv
    FROM users u LEFT JOIN orders o ON u.user_id = o.user_id
    GROUP BY u.channel
),
ChannelCAC AS (
    SELECT channel, SUM(spend) AS total_spend FROM marketing_spend GROUP BY channel
)
SELECT l.channel, l.total_users, c.total_spend,
    ROUND(c.total_spend * 1.0 / l.total_users, 2) AS cac,
    l.ltv,
    CASE WHEN l.ltv > ROUND(c.total_spend * 1.0 / l.total_users, 2) THEN 'Окупается' ELSE 'Убыток' END AS roi_status
FROM ChannelLTV l JOIN ChannelCAC c ON l.channel = c.channel;
