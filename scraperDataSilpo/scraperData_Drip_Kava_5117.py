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
    """Функція для отримання даних через API."""
    url = f"https://sf-ecom-api.silpo.ua/v1/uk/branches/1edb732e-e075-661c-a325-198a97b604e9/products?limit=47&offset={offset}&deliveryType=SelfPickup&category={category}&includeChildCategories=true&sortBy=popularity&sortDirection=desc"
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

def save_to_excel(data, filename='silpo_products.xlsx'):
    """Функція для запису даних у Excel."""
    if not data:
        print("[ЛОГ] Немає даних для запису у файл.")
        return
    header = ['Назва товару', 'Ціна товару(грн)', 'Вага товару(г)', 'Ціна товару з урахуванням знижки(грн)', 'Стара ціна товару(грн)', 'Відсоток знижки(%)']
    data.sort(key=lambda x: x[0])
    df = pd.DataFrame(data, columns=header)
    df.to_excel(filename, index=False, sheet_name='Products')
    print(f"Файл '{filename}' успішно створено!")

def fetch_and_save_data_api(category, filename='silpo_products_Drip_Kava_5117.xlsx'):
    """Основна функція для переходу між сторінками та збору даних."""
    offset = 0
    product_list = []
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
        offset += 47  # Інкрементуємо offset для наступної сторінки
        if len(products) < 47:
            break  # Якщо отримано менше елементів, ніж limit, значить це остання сторінка

    save_to_excel(product_list, filename)

# Виклик функції
fetch_and_save_data_api('drip-kava-5117')
