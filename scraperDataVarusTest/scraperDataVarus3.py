import requests
import pandas as pd

# Множина для перевірки на дублікати (назва + вага + ціна)
unique_products = set()

def is_duplicate(product_name, weight, price):
    """Перевірка на дублікати товарів."""
    product_key = (product_name, weight, price)  # Унікальний ключ: назва + вага + ціна
    if product_key in unique_products:
        return True
    unique_products.add(product_key)
    return False

def extract_value(value_str):
    """Функція для витягування числових значень з форматуванням до двох знаків після коми."""
    try:
        return f"{float(value_str):.2f}"  # Перетворюємо значення на float і форматируемо з двома знаками після коми
    except ValueError:
        return value_str.strip()  # Якщо не можна перетворити, просто повертаємо значення як є

def fetch_product_data_api(category_id, offset=0):
    """Функція для отримання даних через API."""
    url = f"https://varus.ua/api/catalog/vue_storefront_catalog_2/product_v2/_search?from={offset}&size=40"
    params = {
        "query": {"match": {"category_id": category_id}},
        "from": 0,
        "size": 40
    }


    headers = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Accept": "application/json"
}


    try:       
        response = requests.post(url, json=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        print(f"[ЛОГ] Відповідь API: {data}")

        products = data.get("data", []) if isinstance(data, dict) else []
        for product in products:
            if isinstance(product, dict):
                product_name = product.get('name', 'Невідомо')
                print(f"[ЛОГ] Назва продукту: {product_name}")
            else:
                print(f"[ЛОГ] Невідомий формат продукту: {product}")
    except requests.RequestException as e:
        print(f"[ЛОГ] Помилка запиту до API: {e}")
        return []

def save_to_excel(data, filename='varus_products3.xlsx'):
    """Функція для запису даних у Excel."""
    if not data:
        print("[ЛОГ] Немає даних для запису у файл.")
        return
    header = ['Назва товару', 'Ціна товару(грн)', 'Вага товару(г)', 'Ціна товару зі знижкою(грн)', 'Відсоток знижки(%)']
    data.sort(key=lambda x: x[0])
    df = pd.DataFrame(data, columns=header)
    df.to_excel(filename, index=False, sheet_name='Products')
    print(f"Файл '{filename}' успішно створено!")

def fetch_and_save_data_api(category_id, filename='varus_products3.xlsx'):
    """Основна функція для переходу між сторінками та збору даних."""
    offset = 0
    product_list = []
    while True:
        products = fetch_product_data_api(category_id, offset)
        if not products:
            print("[ЛОГ] Дані не знайдено або помилка при завантаженні.")
            break

        for product in products:
            product_name = product.get('name', 'Невідомо')
            weight = product.get('volume', '') or product.get('weight', '')
            price = extract_value(str(product.get('regular_price', 0)))
            discount_price = product.get('special_price_discount')
            discount_percentage = f"-{discount_price}%" if discount_price else ''

            # Перевірка на дублікати за назвою, вагою та ціною
            if is_duplicate(product_name, weight, price):
                continue

            # Додаємо дані до списку
            product_list.append([product_name, price, weight, discount_price, discount_percentage])
            print(f"Додано: {product_name}, Ціна: {price}, Вага: {weight}, Знижка: {discount_percentage}")

        # Переходимо до наступної сторінки
        offset += 40  # Інкрементуємо offset для наступної сторінки
        if len(products) < 40:
            break  # Якщо отримано менше елементів, ніж limit, значить це остання сторінка

    save_to_excel(product_list, filename)

# Виклик функції
fetch_and_save_data_api(category_id=52907, filename='varus_kava.xlsx')
