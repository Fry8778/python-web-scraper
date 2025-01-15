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

# def extract_value(value):
#     """Перетворює значення на float і форматує з двома знаками після коми."""
#     try:
#         return f"{float(value):.2f}"  # Перетворення на float
#     except (ValueError, TypeError):
#         return value.strip()  # Повернення оригінального значення

def extract_value(value, is_weight=False):
    """
    Перетворює значення на float. 
    Для ваги (is_weight=True) видаляє нулі, 
    для інших чисел додає два десяткові знаки.
    """
    try:
        value = float(value)
        if is_weight:
            return f"{int(value)}" if value.is_integer() else f"{value:.2f}"
        else:
            return f"{value:.2f}"  # Завжди два десяткові знаки
    except (ValueError, TypeError):
        return str(value).strip()  # Повернення оригінального значення


def fetch_product_data_api(category, offset=0):
    """Функція для отримання даних через API Varus або інший API з урахуванням категорії."""
    url = f"https://varus.ua/api/catalog/vue_storefront_catalog_2/product_v2/_search"
    params = {
        "_source_include": "name,weight,sqpp_data_9.price,sqpp_data_9.special_price,sqpp_data_9.special_price_discount,sqpp_data_9.in_stock",
        "from": offset,
        "size": 40,  # Ліміт товарів на сторінку
        "request_format": "search-query",
        "response_format": "compact",
        "shop_id": 9,
        "request": f'{{"_appliedFilters":[{{"attribute":"category_ids","value":{{"in":[{category}]}},"scope":"default"}}]}}'
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get('hits', [])
    except requests.RequestException as e:
        print(f"[ЛОГ] Помилка запиту до API: {e}")
        return []

def save_to_excel(data, filename='varus_products7.xlsx'):
    """Функція для запису даних у Excel."""
    if not data:
        print("[ЛОГ] Немає даних для запису у файл.")
        return
    header = ['Назва товару', 'Ціна товару(грн)', 'Вага товару(г)', 'Ціна товару з урахуванням знижки(грн)', 'Стара ціна товару(грн)', 'Відсоток знижки(%)']
    data.sort(key=lambda x: x[0])
    df = pd.DataFrame(data, columns=header)
    df.to_excel(filename, index=False, sheet_name='Products')
    print(f"Файл '{filename}' успішно створено!")

def fetch_and_save_data_api(category, filename='varus_products7.xlsx'):
    """Основна функція для збору даних і збереження у файл."""
    offset = 0
    product_list = []
    while True:
        products = fetch_product_data_api(category, offset)
        if not products:
            print("[ЛОГ] Дані не знайдено або помилка при завантаженні.")
            break

        for product in products:
            product_name = product.get('name', '').strip()
            price = extract_value(product.get('sqpp_data_9', {}).get('price')) + " грн"
            discount = product.get('sqpp_data_9', {}).get('special_price_discount', '')
            # discount = extract_value(product.get('sqpp_data_9', {}).get('special_price_discount', ''))
            # if discount:
            #     discount += " %"  # Додаємо "%"
            stock_qty = product.get('stock', {}).get('qty', 0)  # Відсутність на складі враховуємо тут
            weight = extract_value(product.get('weight', ''), is_weight=True) + " г"
            price_with_discount = extract_value(product.get('sqpp_data_9', {}).get('special_price', ''))
            if price_with_discount:
                price_with_discount += " грн"  # Додаємо "грн" до ціни зі знижкою

            # Перевірка на наявність товару
            # if not product.get('sqpp_data_9', {}).get('in_stock', False):
            #     print(f"[ЛОГ] Пропущено (відсутній на складі): {product_name}")
            #     continue

            if product.get('sqpp_data_9', {}).get('in_stock', 0) == 0:
                print(f"[ЛОГ] Пропущено (відсутній на складі): {product_name}")
                continue
            
            # Логування інформації про товар
            print(f"[ЛОГ] Назва: {product_name}, Ціна: {price}, Знижка: {discount}%, Ціна зі знижкою: {price_with_discount}, Кількість на складі: {stock_qty}, Вага: {weight}")
            
            # Перевірка на дублікати
            if is_duplicate(product_name, weight, price):
                continue

            # Додаємо дані до списку
            product_list.append([product_name,
                                 price if not discount else '',
                                 weight,
                                 price_with_discount,
                                 price,
                                 f"{discount}%" if discount else ''])

        offset += 40  # Переходимо до наступної сторінки
        if len(products) < 40:
            break  # Остання сторінка

    save_to_excel(product_list, filename)

# Виклик функції для категорії 52907 (наприклад)
fetch_and_save_data_api(52907)
