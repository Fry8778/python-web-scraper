import requests
import pandas as pd 

def fetch_product_data_api(offset=0):
    """
    Функція для отримання даних через API Varus.
    """
    url = "https://varus.ua/api/catalog/vue_storefront_catalog_2/product_v2/_search"
    params = {
        "_source_include": "name,weight,sqpp_data_9.price,sqpp_data_9.special_price,sqpp_data_9.special_price_discount,sqpp_data_9.in_stock",
        "from": offset,
        "size": 40,  # Ліміт товарів на сторінку
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

def process_product_data(products):
    """
    Обробляє дані товарів.
    """
    product_list = []
    
    for product in products:
        # Назва
        name = product.get('name', 'Невідомо')       
               
        # Вага
        weight = product.get('weight', 'Невідомо')
        
        # Ціна
        price = product.get('sqpp_data_9', {}).get('price', 0)
        
        # Ціна зі знижкою
        special_price = product.get('sqpp_data_9', {}).get('special_price', '')
        
        # Відсоток знижки
        discount = product.get('sqpp_data_9', {}).get('special_price_discount', '')
        
        # Наявність на складі
        in_stock = product.get('sqpp_data_9', {}).get('in_stock', False)
        
        product_list.append({
            "Назва": name,           
            "Вага (г)": weight,
            "Ціна (грн)": price,
            "Ціна зі знижкою (грн)": special_price,
            "Відсоток знижки (%)": discount,
            "Наявність": "Є в наявності" if in_stock else "Немає в наявності"
        })
    
    return product_list

def save_to_excel(data, filename='varus_products6.xlsx'):
    """
    Записує дані у файл Excel.
    """
    if not data:
        print("[ЛОГ] Немає даних для запису у файл.")
        return
    
    df = pd.DataFrame(data)
    df.to_excel(filename, index=False, sheet_name='Products')
    print(f"Файл '{filename}' успішно створено!")

def main():
    """
    Основна функція для виклику API, обробки даних та збереження результатів.
    """
    offset = 0
    all_products = []
    
    while True:
        products = fetch_product_data_api(offset)
        if not products:
            break
        all_products.extend(process_product_data(products))
        offset += 40
        if len(products) < 40:  # Якщо це остання сторінка
            break
    
    save_to_excel(all_products)

if __name__ == "__main__":
    main()
