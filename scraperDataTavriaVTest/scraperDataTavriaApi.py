import requests
import pandas as pd

# Унікальний набір товарів для перевірки дублікатів
unique_products = set()

def is_duplicate(product_name, price):
    """Перевірка на дублікати товарів."""
    product_key = (product_name, price)
    if product_key in unique_products:
        return True
    unique_products.add(product_key)
    return False

def extract_value(value, unit=""):
    """Перетворює числове значення у відформатований текст з одиницею."""
    try:
        if value is None:
            return ''
        value = float(value)
        if unit:
            return f"{value:.0f} {unit}"
        return f"{value:.2f} грн"
    except (ValueError, TypeError):
        return str(value).strip()

def fetch_product_data_api(page=1, limit=100):
    """Функція для отримання даних через API Varus."""
    url = "https://deadpool.special-sailfish.instaleap.io/api/v3"
    headers = {
        "Accept": "*/*",
        "Accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7,uk;q=0.6",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Referer": "https://www.tavriav.ua/ca/%D1%87%D0%B0%D0%B8-%D0%BA%D0%B0%D0%B2%D0%B0-%D1%82%D0%B0-%D0%BA%D0%B0%D0%BA%D0%B0%D0%BE/%D0%BA%D0%B0%D0%B2%D0%BE%D0%B2%D1%96-%D0%BD%D0%B0%D0%BF%D0%BE%D1%96/9829/9830",
    }
    params = {        
        "size": limit,
        "from": (page - 1) * limit,
        # "request": (
        #     '{"_appliedFilters":['
        #     '{"attribute":"category_ids","value":{"in":[52907]},"scope":"default"},'
        #     '{"attribute":"forcoffeebeans_typecoffeebeans","value":{"in":["4663"]},"scope":"catalog"},'
        #     '{"attribute":"sqpp_data_9.in_stock","value":{"or":true},"scope":"default"}'
        #     ']}'    
        # ),
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        print(f"[ЛОГ] URL запиту: {response.url}")
        response.raise_for_status()
        data = response.json()
        return data.get('data', {})
    except requests.RequestException as e:
        print(f"[ЛОГ] Помилка запиту до API: {e}")
        return []

def save_to_excel(data, filename='tavriaV_kava_v_zernakh.xlsx'):
    """Функція для запису даних у Excel."""
    if not data:
        print("[ЛОГ] Немає даних для запису у файл.")
        return
    header = ['Назва товару', 'Ціна товару (грн)', 'Вага товару (г)', 'Ціна товару з урахуванням знижки (грн)', 'Стара ціна товару (грн)', 'Відсоток знижки (%)']
    data.sort(key=lambda x: x[0])
    df = pd.DataFrame(data, columns=header)
    df.to_excel(filename, index=False, sheet_name='Products')
    print(f"Файл '{filename}' успішно створено!")

def fetch_and_save_data_api(filename='tavriaV_kava_v_zernakh.xlsx', limit=100):
    """Основна функція для збору даних і збереження у файл."""
    page = 1
    product_list = []

    while True:
        products = fetch_product_data_api(page, limit)
        if not products:
            print("[ЛОГ] Дані не знайдено або помилка при завантаженні.")
            break

        for product in products:
            product_name = product.get('name', '').strip()
            price = extract_value(product.get('price'))
            # discount = product.get('sqpp_data_9', {}).get('special_price_discount', '')
            price_with_discount = extract_value(product.get('conditions', {}).get('priceBeforeTaxes', ''))

            # Перевірка наявності товару            
            if product.get('stock', 0) == 0:
                print(f"[ЛОГ] Пропущено (відсутній на складі): {product_name}")
                continue
            
            # Логування інформації про товар
            # print(f"[ЛОГ] Назва: {product_name}, Ціна: {price}, Знижка: {discount}%, "
            #       f"Ціна зі знижкою: {price_with_discount}")

            # Перевірка на дублікати
            if is_duplicate(product_name, price):
                continue

            # Додаємо дані до списку
            product_list.append([
                product_name,
                price,              
                price_with_discount,
                price if discount else '',
                f"{discount}%" if discount else ''
            ])

        if len(products) < limit:  # Якщо отримано менше товарів, ніж очікувалося, це остання сторінка
            print("[ЛОГ] Завантажено останню сторінку.")
            break
        page += 1  # Перехід до наступної сторінки

    save_to_excel(product_list, filename)

# Виклик функції
fetch_and_save_data_api(limit=100)
