import pandas as pd
import sqlite3
import os

# Название твоей базы
db_name = 'olist.db'
conn = sqlite3.connect(db_name)

# Список всех файлов Olist
files = [
    'olist_customers_dataset.csv',
    'olist_geolocation_dataset.csv',
    'olist_order_items_dataset.csv',
    'olist_order_payments_dataset.csv',
    'olist_order_reviews_dataset.csv',
    'olist_orders_dataset.csv',
    'olist_products_dataset.csv',
    'olist_sellers_dataset.csv',
    'product_category_name_translation.csv'
]

print("Начинаю импорт данных...")

for file in files:
    if os.path.exists(file):
        # Название таблицы делаем из названия файла (убираем .csv)
        table_name = file.replace('.csv', '')
        
        print(f"Загружаю {file} в таблицу {table_name}...")
        
        # Читаем CSV (у Olist разделитель - запятая)
        df = pd.read_csv(file)
        
        # Записываем в базу (если таблица была, она перезапишется)
        df.to_sql(table_name, conn, if_exists='replace', index=False)
    else:
        print(f"ВНИМАНИЕ: Файл {file} не найден в папке!")

conn.close()
print("Готово! Все таблицы успешно созданы в базе olist.db")
