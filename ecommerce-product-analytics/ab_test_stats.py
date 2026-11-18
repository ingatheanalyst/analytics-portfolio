import pandas as pd
import sqlite3
from scipy import stats

# Подключаемся к базе
conn = sqlite3.connect('ecommerce.db')

# Выгружаем данные по группам
query = """
    SELECT u.ab_group, a.total_revenue 
    FROM users u
    JOIN ab_test_results a ON u.user_id = a.user_id
"""
df = pd.read_sql(query, conn)
conn.close()

# Разделяем на контрольную и тестовую группы
control = df[df['ab_group'] == 'control']['total_revenue']
test = df[df['ab_group'] == 'test']['total_revenue']

# Проводим t-тест Уэлча (так как дисперсии могут быть неравны)
t_stat, p_value = stats.ttest_ind(control, test, equal_var=False)

print(f"Средний ARPU в Control: {control.mean():.2f}")
print(f"Средний ARPU в Test: {test.mean():.2f}")
print(f"T-статистика: {t_stat:.4f}")
print(f"P-value: {p_value:.6f}")

if p_value < 0.05:
    print("Вывод: Разница СТАТИСТИЧЕСКИ ЗНАЧИМА (p < 0.05). Можно внедрять фичу.")
else:
    print("Вывод: Разница НЕ ЗНАЧИМА (p >= 0.05). Прирост может быть случайным.")