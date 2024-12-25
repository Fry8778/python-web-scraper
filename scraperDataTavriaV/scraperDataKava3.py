from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
import random

# Перевірка на дублікати
unique_products = set()

def is_duplicate(product_name):
    if product_name in unique_products:
        return True
    unique_products.add(product_name)
    return False

# Функція для скрапінгу продуктів
def scrape_page(driver, data):
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "product-item"))
        )
        products = driver.find_elements(By.CLASS_NAME, "product-item")

        for product in products:
            try:
                product_name = product.find_element(By.CLASS_NAME, "product-item__name").text.strip()
                if is_duplicate(product_name):
                    continue

                price = product.find_element(By.CLASS_NAME, "product-item__price").text.strip()
                old_price_elements = product.find_elements(By.CLASS_NAME, "product-item__old-price")
                old_price = old_price_elements[0].text.strip() if old_price_elements else ""

                discount_elements = product.find_elements(By.CLASS_NAME, "product-item__discount")
                discount = discount_elements[0].text.strip() if discount_elements else ""

                data.append([product_name, price, old_price, discount])
                print(f"[ЛОГ] Додано: {product_name}, Ціна: {price}")

            except Exception as e:
                print(f"[ЛОГ] Помилка збору даних для продукту: {e}")

    except Exception as e:
        print(f"[ЛОГ] Помилка збору даних: {e}")

    return data

# Функція для скролінгу сторінки вниз
def scroll_down(driver):
    scroll_pause_time = random.uniform(1.5, 3.5)  # Випадковий час паузи
    current_height = driver.execute_script("return document.body.scrollHeight")
    
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause_time)

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == current_height:
            print("[ЛОГ] Додаткових елементів не знайдено. Завантаження завершено.")
            break
        current_height = new_height

# Основний код
base_url = 'https://www.tavriav.ua/ca/%D1%87%D0%B0%D0%B8-%D0%BA%D0%B0%D0%B2%D0%B0-%D1%82%D0%B0-%D0%BA%D0%B0%D0%BA%D0%B0%D0%BE/%D0%BA%D0%B0%D0%B2%D0%BE%D0%B2%D1%96-%D0%BD%D0%B0%D0%BF%D0%BE%D1%96/9829/9830'
options = webdriver.ChromeOptions()
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
options.add_argument('--headless')
options.add_argument('--disable-cache')
options.add_argument('--incognito')
options.add_argument("accept=text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
options.add_argument("accept-language=en-US,en;q=0.5")


with webdriver.Chrome(options=options) as driver:
    driver.get(base_url)
    data = []

    print("[ЛОГ] Початок скролінгу.")
    scroll_down(driver)  # Скролимо сторінку до кінця
    print("[ЛОГ] Завершено скролінг. Початок збору даних.")
    data = scrape_page(driver, data)

    if data:
        header = ['Назва товару', 'Ціна товару', 'Стара ціна', 'Знижка']
        df = pd.DataFrame(data, columns=header)
        output_file = 'tavria_products.xlsx'
        df.to_excel(output_file, index=False, sheet_name='Products')
        print(f"Файл '{output_file}' успішно створено!")
    else:
        print("[ЛОГ] Дані відсутні. Файл не створено.")
