import requests
import pandas as pd

unique_products = set()

def is_duplicate(product_name, weight, price):
    """Перевірка на дублікати товарів."""
    product_key = (product_name, weight, price)
    if product_key in unique_products:
        return True
    unique_products.add(product_key)
    return False

def extract_value(value):
    """Перетворює значення на float і форматує з двома знаками після коми."""
    try:
        return f"{float(value):.2f}"  # Перетворення на float
    except (ValueError, TypeError):
        return value  # Повернення оригінального значення

def fetch_product_data_api(offset=0):
    """Функція для отримання даних через API Varus."""
    url = f"https://varus.ua/api/catalog/vue_storefront_catalog_2/product_v2/_search"
    params = {
        "_source_include": "name,regular_price,special_price_discount,stock.qty,weight",
        "from": offset,
        "size": 39,  # Ліміт товарів на сторінку
        "request_format": "search-query",
        "response_format": "compact",
        "shop_id": 9,
        "request": '{"_appliedFilters":[{"attribute":"category_ids","value":{"in":[52907]},"scope":"default"}]}'
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get('hits', [])
    except requests.RequestException as e:
        print(f"[ЛОГ] Помилка запиту до API: {e}")
        return []

def save_to_excel(data, filename='varus_products.xlsx'):
    """Функція для запису даних у Excel."""
    if not data:
        print("[ЛОГ] Немає даних для запису у файл.")
        return
    header = ['Назва товару', 'Ціна товару (грн)', 'Знижка (%)', 'Кількість на складі', 'Вага']
    data.sort(key=lambda x: x[0])
    df = pd.DataFrame(data, columns=header)
    df.to_excel(filename, index=False, sheet_name='Products')
    print(f"Файл '{filename}' успішно створено!")

def fetch_and_save_data_api(filename='varus_products.xlsx'):
    """Основна функція для збору даних і збереження у файл."""
    offset = 0
    product_list = []
    while True:
        products = fetch_product_data_api(offset)
        if not products:
            print("[ЛОГ] Дані не знайдено або помилка при завантаженні.")
            break

        for product in products:
            product_name = product.get('name', '').strip()
            price = extract_value(product.get('regular_price'))
            discount = product.get('special_price_discount', 0)
            stock_qty = product.get('stock', {}).get('qty', 0)
            weight = extract_value(product.get('weight', ''))

            # Перевірка на дублікати
            if is_duplicate(product_name, weight, price):
                continue

            # Додаємо дані до списку
            product_list.append([product_name, price, discount, stock_qty, weight])
            print(f"Додано: {product_name}, Ціна: {price}, Знижка: {discount}%, Кількість: {stock_qty}, Вага: {weight}")

        offset += 39  # Переходимо до наступної сторінки
        if len(products) < 39:
            break  # Остання сторінка

    save_to_excel(product_list, filename)

# Виклик функції
fetch_and_save_data_api()
