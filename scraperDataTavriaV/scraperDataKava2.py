from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
import random

# Перевірка дублікатів
unique_products = set()

def is_duplicate(product_name):
    if product_name in unique_products:
        return True
    unique_products.add(product_name)
    return False

def scrape_page(driver, data):
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".product-item"))
        )
        products = driver.find_elements(By.CSS_SELECTOR, ".product-item")

        if not products:
            print("[ЛОГ] Продукти не знайдені на сторінці.")
            return data

        for product in products:
            try:
                product_name = product.find_element(By.CSS_SELECTOR, ".product-item__name").text.strip()
                if is_duplicate(product_name):
                    continue

                price = product.find_element(By.CSS_SELECTOR, ".product-item__price").text.strip()
                old_price_elements = product.find_elements(By.CSS_SELECTOR, ".product-item__old-price")
                old_price = old_price_elements[0].text.strip() if old_price_elements else ""

                discount_elements = product.find_elements(By.CSS_SELECTOR, ".product-item__discount")
                discount = discount_elements[0].text.strip() if discount_elements else ""

                data.append([product_name, price, old_price, discount])
                print(f"[ЛОГ] Додано: {product_name}, Ціна: {price}")

            except Exception as e:
                print(f"[ЛОГ] Помилка обробки продукту: {e}")

    except Exception as e:
        print(f"[ЛОГ] Загальна помилка збору даних: {e}")

    return data

def go_to_next_page(driver):
    try:
        next_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.pagination__next"))
        )
        if "disabled" in next_button.get_attribute("class"):
            print("[ЛОГ] Це остання сторінка.")
            return False

        driver.execute_script("arguments[0].click();", next_button)
        time.sleep(random.uniform(2, 5))
        print("[ЛОГ] Перехід на наступну сторінку.")
        return True
    except Exception as e:
        print(f"[ЛОГ] Помилка переходу на наступну сторінку: {e}")
        return False

# Основний код
base_url = 'https://www.tavriav.ua/ca/%D1%87%D0%B0%D0%B8-%D0%BA%D0%B0%D0%B2%D0%B0-%D1%82%D0%B0-%D0%BA%D0%B0%D0%BA%D0%B0%D0%BE/%D0%BA%D0%B0%D0%B2%D0%BE%D0%B2%D1%96-%D0%BD%D0%B0%D0%BF%D0%BE%D1%96/9829/9830'
options = webdriver.ChromeOptions()
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
options.add_argument('--headless')
options.add_argument('--disable-cache')
options.add_argument('--incognito')

with webdriver.Chrome(options=options) as driver:
    driver.get(base_url)
    data = []
    page_number = 1

    while True:
        print(f"[ЛОГ] Завантаження сторінки {page_number}.")
        data = scrape_page(driver, data)

        if not go_to_next_page(driver):
            print("[ЛОГ] Завантаження завершено.")
            break
        page_number += 1

    if data:
        header = ['Назва товару', 'Ціна товару', 'Стара ціна', 'Знижка']
        df = pd.DataFrame(data, columns=header)
        output_file = 'tavria_products.xlsx'
        df.to_excel(output_file, index=False, sheet_name='Products')
        print(f"Файл '{output_file}' успішно створено!")
    else:
        print("[ЛОГ] Дані відсутні. Файл не створено.")
