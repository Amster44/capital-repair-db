# -*- coding: utf-8 -*-
"""
Анализ структуры Excel файлов УК
"""
import pandas as pd
import sys

# Открываем файл
df = pd.read_excel('data/uk_data/Сведения по субъекту Татарстан Республика на 02.02.2026.xlsx')

# Выводим все колонки
print(f'Всего колонок: {len(df.columns)}')
print(f'Всего строк: {len(df)}')
print('\nСтруктура файла:')
for i, col in enumerate(df.columns):
    print(f'Колонка {i}: {col}')

# Пример первой строки
print('\n\nПример первой строки (непустые поля):')
if len(df) > 0:
    for i, col in enumerate(df.columns):
        val = df.iloc[0][col]
        if pd.notna(val) and str(val).strip() != '':
            print(f'{i}. {col}: {str(val)[:150]}')
