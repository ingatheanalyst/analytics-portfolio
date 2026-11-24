import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

st.set_page_config(page_title="Olist E-commerce Dashboard", layout="wide")
st.title("📊 Дашборд E-commerce (Olist)")
st.markdown("Анализ продаж, категорий и качества доставки на основе реальных данных.")

# --- БОКОВАЯ ПАНЕЛЬ С ФИЛЬТРАМИ ---
st.sidebar.header("Фильтры")

# 1. Загружаем все данные для фильтров (штаты и даты)
@st.cache_data
def load_filter_data():
    conn = sqlite3.connect('data/olist.db')
    # Получаем уникальные штаты
    states = pd.read_sql("SELECT DISTINCT customer_state FROM customers", conn)['customer_state'].tolist()
    # Получаем минимальную и максимальную дату
    dates = pd.read_sql("SELECT MIN(order_purchase_timestamp) as min_d, MAX(order_purchase_timestamp) as max_d FROM orders", conn)
    conn.close()
    
    min_date = pd.to_datetime(dates['min_d'][0]).date()
    max_date = pd.to_datetime(dates['max_d'][0]).date()
    return states, min_date, max_date

all_states, min_date, max_date = load_filter_data()

# Создаем виджеты в боковой панели
selected_states = st.sidebar.multiselect("Выберите штаты:", options=all_states, default=all_states[:5])
date_range = st.sidebar.date_input("Период:", [min_date, max_date])

# Формируем условие WHERE для SQL на основе выбора
if not selected_states:
    selected_states = all_states # Если ничего не выбрано, показываем все
    
# Превращаем список штатов в строку для SQL: 'SP', 'RJ', 'MG'
states_str = "', '".join(selected_states)

# --- ЗАПРОСЫ К БАЗЕ С УЧЕТОМ ФИЛЬТРОВ ---
@st.cache_data
def load_data(query):
    conn = sqlite3.connect('data/olist.db')
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Формируем базовые условия
date_filter = f"AND o.order_purchase_timestamp >= '{date_range[0]}' AND o.order_purchase_timestamp <= '{date_range[1]} 23:59:59'"
state_filter = f"AND c.customer_state IN ('{states_str}')"

try:
    # 1. Выручка (теперь с джойном клиентов для фильтра по штату)
    df_revenue = load_data(f"""
        SELECT STRFTIME('%Y-%m', o.order_purchase_timestamp) AS order_month,
               COUNT(DISTINCT o.order_id) AS total_orders,
               ROUND(SUM(oi.price), 2) AS total_revenue
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        JOIN customers c ON o.customer_id = c.customer_id
        WHERE o.order_status = 'delivered' {date_filter} {state_filter}
        GROUP BY order_month ORDER BY order_month
    """)

    # 2. Топ категорий
    df_categories = load_data(f"""
        SELECT p.product_category_name AS category, ROUND(SUM(oi.price), 2) AS revenue
        FROM order_items oi
        JOIN products p ON oi.product_id = p.product_id
        JOIN orders o ON oi.order_id = o.order_id
        JOIN customers c ON o.customer_id = c.customer_id
        WHERE o.order_status = 'delivered' AND p.product_category_name IS NOT NULL {date_filter} {state_filter}
        GROUP BY category ORDER BY revenue DESC LIMIT 5
    """)

    # 3. Влияние опозданий
    df_delivery = load_data(f"""
        SELECT CASE WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date THEN 'Опоздание' ELSE 'Вовремя' END AS delivery_status,
               ROUND(AVG(r.review_score), 2) AS avg_review_score,
               COUNT(o.order_id) AS total_orders
        FROM orders o
        JOIN order_reviews r ON o.order_id = r.order_id
        JOIN customers c ON o.customer_id = c.customer_id
        WHERE o.order_status = 'delivered' AND o.order_delivered_customer_date IS NOT NULL {date_filter} {state_filter}
        GROUP BY delivery_status
    """)

except Exception as e:
    st.error(f"Ошибка данных: {e}")
    st.stop()

# --- ОТРИСОВКА (Если данных нет из-за фильтров) ---
if df_revenue.empty:
    st.warning("По выбранным фильтрам нет данных. Попробуйте изменить период или штаты.")
    st.stop()

# KPI Карточки
total_rev = df_revenue['total_revenue'].sum()
total_orders = df_revenue['total_orders'].sum()
# Защита от деления на ноль, если по фильтрам нет отзывов
avg_score = (df_delivery['avg_review_score'] * df_delivery[
Plotly express in Python
plotly.com


l_orders']).sum() / df_delivery['total_orders'].sum() if not df_delivery.empty else 0

col1, col2, col3 = st.columns(3)
col1.metric("Общая выручка", f"{total_rev:,.0f} BRL")
col2.metric("Всего заказов", f"{total_orders:,.0f}")
col3.metric("Средний рейтинг", f"{avg_score:.2f} ⭐" if avg_score > 0 else "Нет данных")

st.divider()

# Графики
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Динамика выручки по месяцам")
    fig_rev = px.line(df_revenue, x='order_month', y='total_revenue', 
                      labels={'total_revenue': 'Выручка (BRL)', 'order_month': 'Месяц'},
                      markers=True, color_discrete_sequence=['#2ecc71'])
    st.plotly_chart(fig_rev, width='stretch')

with col_right:
    st.subheader("Топ-5 категорий по выручке")
    fig_cat = px.bar(df_categories, x='revenue', y='category', orientation='h',
                     labels={'revenue': 'Выручка (BRL)', 'category': 'Категория'},
                     color='revenue', color_continuous_scale='Viridis')
    fig_cat.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_cat, width='stretch')

st.subheader("Влияние опозданий на рейтинг клиента")
if not df_delivery.empty:
    fig_del = px.bar(df_delivery, x='delivery_status', y='avg_review_score', text='avg_review_score',
                     labels={'delivery_status': 'Статус доставки', 'avg_review_score': 'Средний рейтинг'},
                     color='delivery_status', color_discrete_map={'Опоздание': '#e74c3c', 'Вовремя': '#2ecc71'})
    fig_del.update_traces(texttemplate='%{text:.2f} ⭐', textposition='outside')
    st.plotly_chart(fig_del, width='stretch')
else:
    st.info("Нет данных по доставке за выбранный период.")

st.caption("Данные: Brazilian E-Commerce Public Dataset by Olist (Kaggle)")'tota
