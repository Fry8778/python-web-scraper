import requests
import pandas as pd

# Унікальний набір товарів для перевірки дублікатів
unique_products = set()

def is_duplicate(product_name, weight, price):
    """Перевірка на дублікати товарів."""
    product_key = (product_name, weight, price)
    if product_key in unique_products:
        return True
    unique_products.add(product_key)
    return False

# def matches_filter(product_name):
#     """Перевірка, чи назва продукту відповідає фільтру."""
#     keywords = ["кава зернова", "кава в зернах"]
#     return any(keyword.lower() in product_name.lower() for keyword in keywords)

  
def extract_value(value, unit=""):
    """Перетворює числове значення у відформатований текст з одиницею."""
    try:
        if value is None:
            return ''
        value = float(value) / 100  # Значення в копійках -> гривні
        if unit == "г":
            return f"{int(value * 100)} {unit}"  # Конвертуємо в грами
        return f"{value:.2f} грн"
    except (ValueError, TypeError):
        return str(value).strip()

    

def fetch_product_data_api(offset=0, limit=30):
    """Функція для отримання даних через API Novus."""
    url = "https://stores-api.zakaz.ua/stores/48201031/categories/coffee-bean/products/"
    headers = {
        "Accept": "*/*",
        "Accept-Language": "uk",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Origin": "https://novus.zakaz.ua",
        "Referer": "https://novus.zakaz.ua/uk/categories/coffee-bean/",
        "x-chain": "novus",
        "x-delivery-type": "pickup",
        "x-version": "63",
    }
    params = {
        "limit": limit,
        "offset": offset,
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        return data  # Повертаємо весь JSON-відповідь
    except requests.RequestException as e:
        print(f"[ЛОГ] Помилка запиту до API: {e}")
        return {}

def save_to_excel(data, filename='scraper_novus_kava_v_zernakh1.xlsx'):
    """Функція для запису даних у Excel."""
    if not data:
        print("[ЛОГ] Немає даних для запису у файл.")
        return
    header = ['Назва товару', 'Ціна товару (грн)', 'Вага товару (г)', 'Ціна товару з урахуванням знижки (грн)', 'Стара ціна товару (грн)', 'Відсоток знижки (%)']
    data.sort(key=lambda x: x[0])
    df = pd.DataFrame(data, columns=header)
    df.to_excel(filename, index=False, sheet_name='Products')
    print(f"Файл '{filename}' успішно створено!")

def fetch_and_save_data_api(filename='scraper_novus_kava_v_zernakh1.xlsx', limit=30):
    """Основна функція для збору даних і збереження у файл."""
    offset = 0
    product_list = []
    total_count = None  # Загальна кількість товарів

    while True:
        data = fetch_product_data_api(offset, limit)
        if not data:
            print("[ЛОГ] Дані не знайдено або помилка при завантаженні.")
            break

        if total_count is None:
            total_count = data.get("count", 0)
            print(f"[ЛОГ] Загальна кількість товарів: {total_count}")

        products = data.get("results", [])
        print(f"[ЛОГ] Отримано {len(products)} товарів з offset={offset}")
        if not products:
            break

        for product in products:
            product_name = product.get('title', '').strip()
            price = extract_value(product.get('price'))
            old_price = product.get('discount', {}).get('old_price')
            discount = product.get('discount', {}).get('value', '')
            weight = extract_value(product.get('weight', ''), unit="г")           
            price_with_discount = (
                extract_value(old_price) if old_price else ""
            )

            # Фільтрація за ключовими словами
            # if not matches_filter(product_name):
            #     print(f"[ЛОГ] Пропущено через невідповідність фільтру: {product_name}")
            #     continue

            # Логування інформації про товар
            print(f"[ЛОГ] Назва: {product_name}, Ціна: {price}, Знижка: {discount}%, Ціна зі знижкою: {price_with_discount}, Вага: {weight}")

            # Перевірка на дублікати
            if is_duplicate(product_name, weight, price):
                print(f"[ЛОГ] Пропущено дублікат: {product_name}, {weight}, {price}")
                continue

            # Додаємо дані до списку
            product_list.append([
                product_name,
                price if not discount else '',
                weight,
                price_with_discount,
                 extract_value(old_price) if old_price else '',
                f"{discount}%" if discount else ''
            ])

        offset += limit
        if offset >= total_count:
            print("[ЛОГ] Завантажено всі товари.")
            break

    save_to_excel(product_list, filename)

# Виклик функції
fetch_and_save_data_api(limit=30)
