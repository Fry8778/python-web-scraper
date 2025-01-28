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
    """Функція для отримання даних через API."""
    url = "https://deadpool.special-sailfish.instaleap.io/api/v3"
    headers = {
        "Accept": "*/*",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Content-Type": "application/json; charset=utf-8",
    }
    payload = {
        "operationName": "GetProductsByCategory",
        "variables": {
            "getProductsByCategoryInput": {
                "categoryReference": "9830",  # Ваше значення категорії
                "clientId": "TAVRIA_UA",
                "storeReference": "449",
                "currentPage": page,
                "pageSize": limit,
                "filters": {},
            }
        },
        "query": """
        query GetProductsByCategory($getProductsByCategoryInput: GetProductsByCategoryInput!) {
          getProductsByCategory(getProductsByCategoryInput: $getProductsByCategoryInput) {
            category {
              products {
                name
                price
                stock
                promotion {
                  conditions {
                    price
                  }
                }
              }
            }
          }
        }
        """
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return data.get('data', {}).get('getProductsByCategory', {}).get('category', {}).get('products', [])
    except requests.RequestException as e:
        print(f"[ЛОГ] Помилка запиту до API: {e}")
        return []

def save_to_excel(data, filename='tavriaV_kava_v_zernakh_api2.xlsx'):
    """Функція для запису даних у Excel."""
    if not data:
        print("[ЛОГ] Немає даних для запису у файл.")
        return

    header = ['Назва товару', 'Ціна товару (грн)', 'Ціна товару з урахуванням знижки (грн)', 'Стара ціна товару (грн)', 'Відсоток знижки (%)']
    data.sort(key=lambda x: x[0])
    df = pd.DataFrame(data, columns=header)
    df.to_excel(filename, index=False, sheet_name='Products')
    print(f"Файл '{filename}' успішно створено!")

def fetch_and_save_data_api(filename='tavriaV_kava_v_zernakh_api2.xlsx', limit=100):
    """Основна функція для збору даних і збереження у файл."""
    page = 1
    product_list = []

    while True:
        products = fetch_product_data_api(page, limit)
        if not products:
            print("[ЛОГ] Дані не знайдено або помилка при завантаженні.")
            break

        print(f"[ЛОГ] Завантажено продуктів: {len(products)} на сторінці {page}")

        for product in products:
            try:
                product_name = product.get('name', '').strip()
                price = extract_value(product.get('price'))
               
               # Обробка ціни зі знижкою
                price_with_discount = None
                promotion = product.get('promotion')
                if promotion and 'conditions' in promotion and promotion['conditions']:
                    price_with_discount = extract_value(promotion['conditions'][0].get('price', price))
                else:
                    price_with_discount = ''  # Якщо знижки немає
                    
                # Перевірка на наявність товару на складі
                # if product.get('stock', 0) <= 0:
                #     print(f"[ЛОГ] Пропущено (відсутній на складі): {product_name}, stock: {product.get('stock', 'N/A')}")
                #     continue

                # Перевірка на дублікати
                if is_duplicate(product_name, price):
                    print(f"[ЛОГ] Пропущено (дублікат): {product_name}")
                    continue

                # Додавання продукту до списку
                product_list.append([product_name,                                    
                                    price if not price_with_discount else '',  # Якщо є знижка, це поле порожнє
                                    price_with_discount,  # Ціна зі знижкою (або порожньо)
                                    price if price_with_discount else '',  # Стара ціна    
                                                                   
                                     ])
            except Exception as e:
                print(f"[ЛОГ] Помилка обробки продукту: {e}")
        
        if len(products) < limit:
            print("[ЛОГ] Завантажено останню сторінку.")
            break

        page += 1

    print(f"[ЛОГ] Усього продуктів для запису: {len(product_list)}")
    save_to_excel(product_list, filename)

# Виклик функції
fetch_and_save_data_api(limit=100)
