import requests 
import pandas as pd
import re

# Множина для перевірки на дублікати
unique_products = set()

def is_duplicate(product_name):
    if product_name in unique_products:
        return True
    unique_products.add(product_name)
    return False

# Функція для витягування лише числових значень
def extract_value(value_str):
    match = re.match(r'(\d+)', value_str.strip())
    if match:
        return match.group(1)  # Числове значення
    return value_str.strip()

# Функція для отримання даних через API
def fetch_product_data_api(category, offset=0):
    url = f"https://sf-ecom-api.silpo.ua/v1/uk/branches/1edb732e-e075-661c-a325-198a97b604e9/products?limit=47&offset={offset}&deliveryType=SelfPickup&category={category}&includeChildCategories=true&sortBy=popularity&sortDirection=desc"
    # url = f"https://sf-ecom-api.silpo.ua/v1/uk/branches/1edb732e-e075-661c-a325-198a97b604e9/products?limit=47&offset={offset}0&deliveryType=SelfPickup&category={category}&includeChildCategories=true&sortBy=popularity&sortDirection=desc"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if 'products' in data:
            return data['products']
        elif 'items' in data:
            print("[ЛОГ] Використовуються дані з поля 'items'.")
            return data['items']
        else:
            print(f"[ЛОГ] Ключі 'products' та 'items' відсутні у відповіді API. Повна відповідь: {data}")
            return []
    except requests.RequestException as e:
        print(f"[ЛОГ] Помилка запиту до API: {e}")
        return []

# Запис у Excel
def save_to_excel(data, filename='silpo_products.xlsx'):
    if not data:
        print("[ЛОГ] Немає даних для запису у файл.")
        return
    header = ['Назва товару', 'Ціна товару(грн)', 'Вага товару(г)', 'Стара ціна товару(грн)', 'Відсоток знижки(%)']
    # data.sort(key=lambda x: x[0])
    df = pd.DataFrame(data, columns=header)
    df.to_excel(filename, index=False, sheet_name='Products')
    print(f"Файл '{filename}' успішно створено!")

# Основний код для переходу між сторінками
def fetch_and_save_data_api(category, filename='silpo_products_api.xlsx'):
    offset = 0
    quotes = []
    while True:
        products = fetch_product_data_api(category, offset)
        if not products:
            print("[ЛОГ] Дані не знайдено або помилка при завантаженні.")
            break

        for product in products:
            # Пропускаємо товари з нульовим запасом
            if product.get('stock', 0) == 0:
                print(f"[ЛОГ] Пропущено (відсутній на складі): {product['title']}")
                continue

            product_name = product['title']
            if is_duplicate(product_name):
                continue

            # Отримуємо ціну без одиниці виміру
            price = extract_value(str(product['displayPrice']))
            old_price = extract_value(str(product.get('displayOldPrice', '')))
            weight_str = product['displayRatio']
            weight = extract_value(weight_str)

            # Обчислення знижки
            if product.get('displayOldPrice'):
                discount = round((float(product['displayOldPrice']) - float(product['displayPrice'])) / float(product['displayOldPrice']) * 100)
                discount_str = f"{discount}"
            else:
                discount_str = ''

            if discount_str == '0%' or discount_str == '':
                old_price = ''
                discount_str = ''

            # Додаємо дані в список
            quotes.append([product_name, price, weight, old_price, discount_str])
            print(f"Додано: {product_name}, Ціна: {price}, Вага: {weight}, Знижка: {discount_str}")

        # Переходимо до наступної сторінки
        offset += 47  # Інкрементуємо offset для наступної сторінки
        if len(products) < 47:
            break  # Якщо отримано менше елементів, ніж limit, значить це остання сторінка

    save_to_excel(quotes, filename)

# Виклик функції
fetch_and_save_data_api('kava-v-zernakh-5111')
# fetch_and_save_data_api('drip-kava-5117')
