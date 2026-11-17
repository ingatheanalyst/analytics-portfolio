import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 1. Загружаем данные (напрямую из CSV, чтобы не подключать базу)
df_dogs = pd.read_csv('dogbase.csv', sep=';') # проверь разделитель
df_champ = pd.read_csv('champ.csv', sep=';')

# Объединяем
df = pd.merge(df_champ, df_dogs, on='Dog_id')

# Очищаем от букв, чтобы графики строились
for col in ['A', 'B', 'C', 'Total']:
    df[col] = pd.to_numeric(df[col], errors='coerce')
df_clean = df.dropna(subset=['Total']).copy()

# --- ГРАФИК 1: Топ-5 пород по среднему баллу (С ФИЛЬТРОМ И МАСШТАБОМ) ---
plt.figure(figsize=(10, 5))

# 1. Фильтруем породы с >= 10 выступлениями
breed_counts = df_clean['Breed'].value_counts()
popular_breeds = breed_counts[breed_counts >= 10].index
df_filtered = df_clean[df_clean['Breed'].isin(popular_breeds)]

# 2. Считаем средний балл
top_breeds = df_filtered.groupby('Breed')['Total'].mean().sort_values(ascending=False).head(5)

# 3. Строим график
sns.barplot(x=top_breeds.index, y=top_breeds.values, palette="viridis")

# 4. ЗУМИМ ОСЬ Y (масштаб)
# Берем минимальное значение и отнимаем 10, чтобы столбики не упирались в край
min_val = top_breeds.min() - 10 
max_val = top_breeds.max() + 5  # Добавляем чуть-чуть сверху
plt.ylim(min_val, max_val)

plt.title('Топ-5 пород по среднему итоговому баллу')
plt.ylabel('Средний балл')
plt.xticks(rotation=45)
plt.savefig('chart_breeds.png', bbox_inches='tight') 
plt.show()

# --- ГРАФИК 2: Распределение оценок за След (А) ---
plt.figure(figsize=(10, 5))
sns.histplot(df_clean['A'], bins=15, kde=True, color='blue')
plt.title('Распределение баллов за раздел А (След)')
plt.xlabel('Баллы')
plt.ylabel('Количество собак')
plt.savefig('chart_scores.png', bbox_inches='tight') # Сохраняем как картинку
plt.show()

print("Готово! Графики сохранены как chart_breeds.png и chart_scores.png")