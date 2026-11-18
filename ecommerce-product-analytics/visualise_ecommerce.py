import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns

# Подключаемся к базе
conn = sqlite3.connect('ecommerce.db')
sns.set_theme(style="whitegrid")

# --- ГРАФИК 1: Воронка продаж ---
query_funnel = """
    SELECT 
        '1. Просмотр' as step, COUNT(DISTINCT user_id) as users FROM events WHERE event_type = 'view'
    UNION ALL
    SELECT '2. Клик', COUNT(DISTINCT user_id) FROM events WHERE event_type = 'click'
    UNION ALL
    SELECT '3. Корзина', COUNT(DISTINCT user_id) FROM events WHERE event_type = 'add_to_cart'
    UNION ALL
    SELECT '4. Покупка', COUNT(DISTINCT user_id) FROM events WHERE event_type = 'purchase'
"""
df_funnel = pd.read_sql(query_funnel, conn)

plt.figure(figsize=(10, 5))
sns.barplot(x='step', y='users', data=df_funnel, palette='Blues_d')
plt.title('Воронка продаж E-commerce')
plt.ylabel('Количество уникальных пользователей')
plt.xlabel('')
plt.savefig('chart_funnel.png', bbox_inches='tight')
plt.show()

# --- ГРАФИК 2: A/B-тест (сравнение ARPU) ---
query_ab = """
    SELECT u.ab_group, AVG(a.total_revenue) as arpu
    FROM users u
    JOIN ab_test_results a ON u.user_id = a.user_id
    GROUP BY u.ab_group
"""
df_ab = pd.read_sql(query_ab, conn)
conn.close()

plt.figure(figsize=(8, 5))
sns.barplot(x='ab_group', y='arpu', data=df_ab, palette=['gray', 'green'])
plt.title('Сравнение ARPU: Control vs Test')
plt.ylabel('Средний доход на пользователя (руб.)')
plt.xlabel('Группа')
plt.savefig('chart_ab_test.png', bbox_inches='tight')
plt.show()

print("Готово! Графики сохранены как chart_funnel.png и chart_ab_test.png")