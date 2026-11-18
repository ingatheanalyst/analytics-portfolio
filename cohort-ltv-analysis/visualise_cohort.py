import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns

# Подключаемся к базе
conn = sqlite3.connect('cohort.db')

# Вставляем наш идеальный SQL
query = """
WITH UserCohorts AS (
    SELECT user_id, STRFTIME('%Y-%m', reg_date) AS cohort_month
    FROM users
),
CohortBase AS (
    SELECT cohort_month, COUNT(user_id) AS total_users
    FROM UserCohorts
    GROUP BY cohort_month
),
ReturningUsers AS (
    SELECT 
        uc.cohort_month,
        (CAST(STRFTIME('%Y', o.order_date) AS INTEGER) - CAST(STRFTIME('%Y', u.reg_date) AS INTEGER)) * 12 + 
        (CAST(STRFTIME('%m', o.order_date) AS INTEGER) - CAST(STRFTIME('%m', u.reg_date) AS INTEGER)) AS month_diff,
        COUNT(DISTINCT o.user_id) AS returned_users
    FROM orders o
    JOIN users u ON o.user_id = u.user_id
    JOIN UserCohorts uc ON o.user_id = uc.user_id
    GROUP BY uc.cohort_month, month_diff
)
SELECT 
    b.cohort_month,
    r.month_diff,
    r.returned_users,
    b.total_users,
    ROUND((r.returned_users * 100.0) / b.total_users, 1) AS retention_rate
FROM CohortBase b
JOIN ReturningUsers r ON b.cohort_month = r.cohort_month
ORDER BY b.cohort_month, r.month_diff;
"""

# Загружаем результат
df = pd.read_sql(query, conn)
conn.close()

# Готовим данные для тепловой карты (Pivot)
pivot = df.pivot(index='cohort_month', columns='month_diff', values='retention_rate').fillna(0)

# Строим график
plt.figure(figsize=(12, 6))
# annot=True пишет проценты, fmt=".1f" оставляет один знак после запятой
sns.heatmap(pivot, annot=True, fmt=".1f", cmap="Blues", cbar_kws={'label': 'Retention Rate, %'})
plt.title('Когортный анализ: Retention по месяцам')
plt.ylabel('Когорта (месяц регистрации)')
plt.xlabel('Месяц жизни')

# Сохраняем картинку
plt.savefig('chart_retention.png', bbox_inches='tight')
plt.show()

print("Готово! Сохранено как chart_retention.png")