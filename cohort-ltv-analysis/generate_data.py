import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

np.random.seed(42)
random.seed(42)

# 1. Генерация пользователей (1000 юзеров за 6 месяцев)
users = []
channels = ['organic', 'paid_ads', 'referral']
for i in range(1, 1001):
    reg_date = datetime(2025, 1, 1) + timedelta(days=random.randint(0, 180))
    channel = random.choice(channels)
    users.append([i, reg_date.date(), channel])

df_users = pd.DataFrame(users, columns=['user_id', 'reg_date', 'channel'])
df_users.to_csv('users.csv', index=False, sep=';')

# 2. Генерация заказов (чем больше времени прошло, тем меньше вероятность покупки)
orders = []
order_id = 1
for user in users:
    user_id, reg_date, channel = user
    # Вероятность покупки в первый месяц (зависит от канала)
    prob_buy = 0.4 if channel == 'organic' else (0.2 if channel == 'referral' else 0.3)
    
    if random.random() < prob_buy:
        order_date = reg_date + timedelta(days=random.randint(0, 30))
        amount = round(random.uniform(500, 3000), 2)
        orders.append([order_id, user_id, order_date, amount])
        order_id += 1
        
        # Вероятность повторной покупки (Retention)
        if random.random() < 0.3: 
            order_date2 = order_date + timedelta(days=random.randint(30, 60))
            orders.append([order_id, user_id, order_date2, round(random.uniform(500, 3000), 2)])
            order_id += 1

df_orders = pd.DataFrame(orders, columns=['order_id', 'user_id', 'order_date', 'amount'])
df_orders.to_csv('orders.csv', index=False, sep=';')

# 3. Затраты на маркетинг (CAC)
marketing = [
    ['2025-01-01', 'paid_ads', 50000],
    ['2025-02-01', 'paid_ads', 60000],
    ['2025-03-01', 'paid_ads', 55000],
    ['2025-01-01', 'referral', 10000],
    ['2025-02-01', 'referral', 15000],
    ['2025-03-01', 'referral', 12000]
]
df_marketing = pd.DataFrame(marketing, columns=['month', 'channel', 'spend'])
df_marketing.to_csv('marketing_spend.csv', index=False, sep=';')

print("Данные сгенерированы: users.csv, orders.csv, marketing_spend.csv")