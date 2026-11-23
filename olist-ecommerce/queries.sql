-- ==========================================
-- ПРОЕКТ: Olist E-commerce Analytics
-- ФАЙЛ: queries.sql
-- ОПИСАНИЕ: Основные запросы для дашборда и анализа
-- ==========================================

-- 1. Выручка и количество заказов по месяцам
-- Зачем: Понять сезонность и общий тренд продаж.
-- Фишка: Использую STRFTIME, чтобы сгруппировать данные по месяцам (YYYY-MM).
SELECT 
    STRFTIME('%Y-%m', o.order_purchase_timestamp) AS order_month,
    COUNT(DISTINCT o.order_id) AS total_orders,
    ROUND(SUM(oi.price), 2) AS total_revenue
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.order_status = 'delivered' -- Берем только успешно доставленные
GROUP BY order_month
ORDER BY order_month;

-- 2. Топ-5 категорий товаров по выручке (Оконная функция)
-- Зачем: Понять, на чем компания зарабатывает больше всего.
-- Фишка: Считаю общую выручку по категориям, а потом через RANK() присваиваю места.
WITH CategoryRevenue AS (
    SELECT 
        p.product_category_name AS category,
        SUM(oi.price) AS total_revenue
    FROM order_items oi
    JOIN products p ON oi.product_id = p.product_id
    JOIN orders o ON oi.order_id = o.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY category
)
SELECT 
    category,
    ROUND(total_revenue, 2) AS revenue,
    RANK() OVER (ORDER BY total_revenue DESC) AS category_rank
FROM CategoryRevenue
WHERE category IS NOT NULL -- Отсекаю пустые категории
LIMIT 5;

-- 3. RFM-сегментация клиентов (CTE)
-- Зачем: Найти VIP-клиентов и понять, кого нужно возвращать (one-time buyers).
-- Фишка: Разбиваю клиентов на группы по частоте покупок (Frequency) и сумме (Monetary).
WITH CustomerStats AS (
    SELECT 
        c.customer_unique_id,
        MAX(o.order_purchase_timestamp) AS last_purchase_date,
        COUNT(DISTINCT o.order_id) AS frequency,
        SUM(oi.price) AS monetary
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id
)
SELECT 
    customer_unique_id,
    frequency,
    ROUND(monetary, 2) AS total_spent,
    CASE 
        WHEN frequency >= 3 AND monetary > 500 THEN 'VIP'
        WHEN frequency >= 2 THEN 'Loyal'
        ELSE 'One-time buyer'
    END AS customer_segment
FROM CustomerStats
ORDER BY monetary DESC
LIMIT 100;

-- 4. Влияние опозданий доставки на оценку клиента
-- Зачем: Проверить гипотезу, что из-за задержек падает рейтинг (и бизнес теряет клиентов).
-- Фишка: Сравниваю факт доставки с ожидаемой датой и джойню с таблицей отзывов.
SELECT 
    CASE 
        -- Если факт доставки позже ожидаемой даты - это опоздание
        WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date THEN 'Late'
        ELSE 'On Time'
    END AS delivery_status,
    ROUND(AVG(r.review_score), 2) AS avg_review_score,
    COUNT(o.order_id) AS total_orders
FROM orders o
JOIN order_reviews r ON o.order_id = r.order_id
WHERE o.order_status = 'delivered' 
  AND o.order_delivered_customer_date IS NOT NULL
GROUP BY delivery_status;

-- 5. Когортный анализ Retention (Удержание)
-- Зачем: Понять, возвращаются ли клиенты после первой покупки.
-- Фишка: Считаю месяц первого заказа (когорту), а затем разницу в месяцах до следующих заказов.
WITH CustomerFirstOrder AS (
    SELECT 
        c.customer_unique_id,
        MIN(STRFTIME('%Y-%m', o.order_purchase_timestamp)) AS cohort_month
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    GROUP BY c.customer_unique_id
),
OrderActivity AS (
    SELECT 
        c.customer_unique_id,
        f.cohort_month,
        STRFTIME('%Y-%m', o.order_purchase_timestamp) AS order_month,
        -- Математика для разницы в месяцах в SQLite
        (CAST(STRFTIME('%Y', o.order_purchase_timestamp) AS INT) - CAST(SUBSTR(f.cohort_month, 1, 4) AS INT)) * 12 + 
        (CAST(STRFTIME('%m', o.order_purchase_timestamp) AS INT) - CAST(SUBSTR(f.cohort_month, 6, 2) AS INT)) AS month_diff
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    JOIN


Order f ON c.customer_unique_id = f.customer_unique_id
)
SELECT 
    cohort_month,
    month_diff,
    COUNT(DISTINCT customer_unique_id) AS active_customers
FROM OrderActivity
GROUP BY cohort_month, month_diff
ORDER BY cohort_month, month_diff; CustomerFirst
