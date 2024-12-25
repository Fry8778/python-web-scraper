import requests
import pandas as pd
from urllib.parse import quote_plus

# Множина для перевірки на дублікати
unique_products = set()

def is_duplicate(product_name):
    """Перевірка на дублікати товарів."""
    if product_name in unique_products:
        return True
    unique_products.add(product_name)
    return False

def extract_value(value_str):
    """Функція для витягування числових значень з форматуванням до двох знаків після коми."""
    try:
        return f"{float(value_str):.2f}"  # Перетворюємо значення на float і форматируемо з двома знаками після коми
    except ValueError:
        return value_str.strip()  # Якщо не можна перетворити, просто повертаємо значення як є

def fetch_product_data_api(category, page=1):
    """Функція для отримання даних через API."""
    url = "https://deadpool.special-sailfish.instaleap.io/api/v3"
    # Кодуємо параметри для коректного запиту
    params = {
        'category': quote_plus(category),  # Кодуємо категорію
        'page': page  # Використовуємо параметр 'page' для пагінації
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        # Перевіряємо, чи є дані у getProductsByCategory
        if 'data' in data and 'getProductsByCategory' in data['data']:
            pagination = data['data']['getProductsByCategory'].get('pagination', {})
            total_pages = pagination.get('pages', 1)
            products = data['data']['getProductsByCategory'].get('products', [])
            return products, total_pages
        else:
            print(f"[ЛОГ] Дані не знайдено у 'getProductsByCategory'. Повна відповідь: {data}")
            return [], 0
    except requests.RequestException as e:
        print(f"[ЛОГ] Помилка запиту до API: {e}")
        return [], 0

def save_to_excel(data, filename='products.xlsx'):
    """Функція для запису даних у Excel."""
    if not data:
        print("[ЛОГ] Немає даних для запису у файл.")
        return
    header = ['Назва товару', 'Ціна товару(грн)', 'Вага товару(г)', 'Ціна товару з урахуванням знижки(грн)', 'Стара ціна товару(грн)', 'Відсоток знижки(%)']
    data.sort(key=lambda x: x[0])
    df = pd.DataFrame(data, columns=header)
    df.to_excel(filename, index=False, sheet_name='Products')
    print(f"Файл '{filename}' успішно створено!")

def fetch_and_save_data_api(category, filename='products.xlsx'):
    """Основна функція для переходу між сторінками та збору даних."""
    page = 1
    product_list = []
    while True:
        products, total_pages = fetch_product_data_api(category, page)
        if not products:
            print("[ЛОГ] Дані не знайдено або помилка при завантаженні.")
            break

        for product in products:
            # Пропускаємо товари з нульовим запасом
            if product.get('stock', 0) == 0:
                print(f"[ЛОГ] Пропущено (відсутній на складі): {product['name']}")
                continue

            product_name = product['name']
            if is_duplicate(product_name):
                continue

            # Отримуємо ціну з урахуванням можливих значень None
            if product.get('displayOldPrice') and product.get('displayPrice'):
                old_price = extract_value(str(product['displayOldPrice'])) + " грн"
                price_with_discount = extract_value(str(product['displayPrice'])) + " грн"
                discount = round((float(product['displayOldPrice']) - float(product['displayPrice'])) / float(product['displayOldPrice']) * 100)
                discount_str = f"-{discount} %"
            else:
                old_price = ''
                price_with_discount = ''
                discount_str = ''

            # Отримуємо вагу товару
            weight_str = product.get('displayRatio', '')
            weight = extract_value(weight_str) if weight_str else ''

            # Визначаємо, чи записувати ціну в колонку "Ціна товару"
            price = price_with_discount if discount_str else extract_value(str(product.get('displayPrice', 0))) + " грн"

            # Додаємо дані до списку
            product_list.append([product_name, price if not discount_str else '', weight, price_with_discount, old_price, discount_str])
            print(f"Додано: {product_name}, Ціна: {price}, Вага: {weight}, Відсоток знижки: {discount_str}")

        # Переходимо до наступної сторінки
        if page >= total_pages:
            break  # Якщо поточна сторінка дорівнює або більша за загальну кількість сторінок, припиняємо
        page += 1  # Інкрементуємо сторінку для наступного запиту

    save_to_excel(product_list, filename)

# Виклик функції
fetch_and_save_data_api('Кавові напої')
