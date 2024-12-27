import requests
import pandas as pd

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

def fetch_product_data_api(category, offset=0):
    """Функція для отримання даних через API Таврія."""
    url = "https://deadpool.special-sailfish.instaleap.io/api/v3"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Content-Type": "application/json",
        "Accept": "*/*",
        "Origin": "https://www.tavriav.ua",
        "Referer": f"https://www.tavriav.ua/ca/{category}",
    }
    
    body = {
        "operationName": "GetProductsByCategory",
        "variables": {
            "getProductsByCategoryInput": {
                "categoryReference": category,
                "categoryId": "null",
                "clientId": "TAVRIA_UA",
                "storeReference": "449",
                "currentPage": 1,
                "pageSize": 47,
                "filters": {},
                "googleAnalyticsSessionId": "",
            }
        },
        "query": """
            query GetProductsByCategory($getProductsByCategoryInput: GetProductsByCategoryInput!) {
                getProductsByCategory(getProductsByCategoryInput: $getProductsByCategoryInput) {
                    category {
                        name
                        reference
                        products {
                            name
                            price
                            displayPrice
                            displayOldPrice
                            displayRatio
                            stock
                            description
                        }
                    }
                }
            }
        """
    }
    
    try:
        response = requests.post(url, json=body, headers=headers)
        response.raise_for_status()
        data = response.json()
        if 'data' in data and 'getProductsByCategory' in data['data']:
            return data['data']['getProductsByCategory']['category']['products']
        else:
            print(f"[ЛОГ] Помилка: Немає даних у відповіді API. Повна відповідь: {data}")
            return []
    except requests.RequestException as e:
        print(f"[ЛОГ] Помилка запиту до API: {e}")
        return []

def save_to_excel(data, filename='tavria_products.xlsx'):
    """Функція для запису даних у Excel."""
    if not data:
        print("[ЛОГ] Немає даних для запису у файл.")
        return
    header = ['Назва товару', 'Ціна товару(грн)', 'Вага товару(г)', 'Ціна товару з урахуванням знижки(грн)', 'Стара ціна товару(грн)', 'Відсоток знижки(%)']
    data.sort(key=lambda x: x[0])
    df = pd.DataFrame(data, columns=header)
    df.to_excel(filename, index=False, sheet_name='Products')
    print(f"Файл '{filename}' успішно створено!")

def fetch_and_save_data_api(category, filename='tavria_products.xlsx'):
    """Основна функція для збору даних і запису їх у файл."""
    product_list = []
    products = fetch_product_data_api(category)

    if not products:
        print("[ЛОГ] Дані не знайдено або помилка при завантаженні.")
        return

    for product in products:
        # Пропускаємо товари з нульовим запасом
        if product.get('stock', 0) == 0:
            print(f"[ЛОГ] Пропущено (відсутній на складі): {product['name']}")
            continue

        product_name = product['name']
        if is_duplicate(product_name):
            continue

        # Отримуємо ціну з урахуванням знижки
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

    save_to_excel(product_list, filename)

# Виклик функції
fetch_and_save_data_api('9829')  # Приклад категорії для Таврії
