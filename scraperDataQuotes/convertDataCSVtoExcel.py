import pandas as pd

# Зчитування CSV-файлу
csv_file = "quotes.csv"  # Замініть на назву вашого файлу
excel_file = "output.xlsx"

# Конвертація в Excel
df = pd.read_csv(csv_file)
df.to_excel(excel_file, index=False, sheet_name="Data")

print(f"Файл успішно збережено як {excel_file}")
