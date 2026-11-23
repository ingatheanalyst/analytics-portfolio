import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

st.set_page_config(page_title="Olist E-commerce Dashboard", layout="wide")
st.title("📊 Дашборд E-commerce (Olist)")
st.markdown("Анализ продаж, категорий и качества доставки на основе реальных данных бразильского маркетплейса.")

@st.cache_data
def load_data(query):
    # Убедись, что база лежит в папке data/
    conn = sqlite3.connect('data/olist.db')
    df = pd.read_sql(query, conn)
    conn.close()
    return df

try:
    df_revenue = load_data("""
        SELECT STRFTIME('%Y-%m', o.order_purchase_timestamp) AS order_month,
               COUNT(DISTINCT o.order_id) AS total_orders,
               ROUND(SUM(oi.price), 2) AS total_revenue
        FROM olist_orders_dataset o
        JOIN olist_order_items_dataset oi ON o.order_id = oi.order_id
        WHERE o.order_status = 'delivered'
        GROUP BY order_month ORDER BY order_month
    """)

    df_categories = load_data("""
        SELECT p.product_category_name AS category, ROUND(SUM(oi.price), 2) AS revenue
        FROM olist_order_items_dataset oi
        JOIN olist_products_dataset p ON oi.product_id = p.product_id
        JOIN olist_orders_dataset o ON oi.order_id = o.order_id
        WHERE o.order_status = 'delivered' AND p.product_category_name IS NOT NULL
        GROUP BY category ORDER BY revenue DESC LIMIT 5
    """)

    df_delivery = load_data("""
        SELECT CASE WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date THEN 'Опоздание' ELSE 'Вовремя' END AS delivery_status,
               ROUND(AVG(r.review_score), 2) AS avg_review_score,
               COUNT(o.order_id) AS total_orders
        FROM olist_orders_dataset o
        JOIN olist_order_reviews_dataset r ON o.order_id = r.order_id
        WHERE o.order_status = 'delivered' AND o.order_delivered_customer_date IS NOT NULL
        GROUP BY delivery_status
    """)

except Exception as e:
    st.error(f"Ошибка загрузки данных. Убедитесь, что база olist.db лежит в папке data/. Ошибка: {e}")
    st.stop()

# --- KPI Карточки ---
total_rev = df_revenue['total_revenue'].sum()
total_orders = df_revenue['total_orders'].sum()
avg_score = (df_delivery['avg_review_score'] * df_delivery['total_orders']).sum() / df_delivery['total_orders'].sum()

col1, col2, col3 = st.columns(3)
col1.metric("Общая выручка", f"{total_rev:,.0f} BRL")
col2.metric("Всего заказов", f"{total_orders:,.0f}")
col3.metric("Средний рейтинг", f"{avg_score:.2f} ⭐")

st.divider()

# --- Графики ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Динамика выручки по месяцам")
    fig_rev = px.line(df_revenue, x='order_month', y='total_revenue', 
                      labels={'total_revenue': 'Выручка (BRL)', 'order_month': 'Месяц'},
                      markers=True, color_discrete_sequence=['#2ecc71'])
    # Заменили use_container_width на width='stretch'
    st.plotly_chart(fig_rev, width='stretch')

with col_right:
    st.subheader("Топ-5 категорий по выручке")
    fig_cat = px.bar(df_categories, x='revenue', y='category', orientation='h',
                     labels={'revenue': 'Выручка (BRL)', 'category': 'Категория'},
                     color='revenue', color_continuous_scale='Viridis')
    fig_cat.update_layout(yaxis={'categoryorder':'total ascending'})
    # Заменили use_container_width на width='stretch'
    st.plotly_chart(fig_cat, width='stretch')

st.subheader("Влияние опозданий на рейтинг клиента")
fig_del = px.bar(df_delivery, x='delivery_status', y='avg_review_score', text='avg_review_score',
                 labels={'delivery_status': 'Статус доставки', 'avg_review_score': 'Средний рейтинг'},
                 color='delivery_status', color_discrete_map={'Опоздание': '#e74c3c', 'Вовремя': '#2ecc71'})
fig_del.update_traces(texttemplate='%{text:.2f} ⭐', textposition='outside')
# Заменили use_container_width на width='stretch'
st.plotly_chart(fig_del, width='stretch')

st.caption("Данные: Brazilian E-Commerce Public Dataset by Olist (Kaggle)")
