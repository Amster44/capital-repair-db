# -*- coding: utf-8 -*-
"""
Анализ реестра поставщиков информации
"""
import pandas as pd

# Открываем файл
df = pd.read_excel('Реестр поставщиков информации от  2026-02-02.xlsx')

print(f'Всего строк: {len(df)}')
print(f'Всего колонок: {len(df.columns)}')

# Смотрим заголовки (они могут быть в первой строке)
print('\nЗаголовки колонок:')
for i, col in enumerate(df.columns):
    print(f'{i}. {col}')

# Первые 3 строки (может быть заголовок в данных)
print('\n\nПервые 3 строки:')
for idx in range(min(3, len(df))):
    print(f'\n--- Строка {idx} ---')
    for i, col in enumerate(df.columns):
        val = df.iloc[idx][col]
        if pd.notna(val):
            print(f'  {i}. {str(val)[:100]}')

# Ищем колонки с телефонами, email, директорами
print('\n\nПоиск колонок с контактами...')
for i, col in enumerate(df.columns):
    col_str = str(col).lower()
    # Проверяем первые несколько строк
    sample_vals = []
    for idx in range(min(10, len(df))):
        val = df.iloc[idx][col]
        if pd.notna(val) and str(val).strip() != '':
            sample_vals.append(str(val)[:50])

    if sample_vals:
        print(f'\nКолонка {i}: {col}')
        print(f'  Примеры: {", ".join(sample_vals[:3])}')
