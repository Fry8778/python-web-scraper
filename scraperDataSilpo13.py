from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
import random

# Множина для перевірки на дублікати
unique_products = set()

def is_duplicate(product_name):
    if product_name in unique_products:
        return True
    unique_products.add(product_name)
    return False

# Функція для збору даних з поточної сторінки
def scrape_page(driver, quotes):
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "product-card__body"))
        )
        products = driver.find_elements(By.CLASS_NAME, "product-card__body")

        if not products:
            print("[ЛОГ] Продукти не знайдені на сторінці.")
            return quotes

        for product in products:
            try:
                product_name = WebDriverWait(product, 5).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "product-card__title"))
                ).text.strip()

                if is_duplicate(product_name):
                    continue

                weight = product.find_element(By.CLASS_NAME, "ft-typo-14-semibold").text.strip()

                # Збір цін і знижок
                price = WebDriverWait(product, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.ft-text-22.ft-font-bold"))
                ).text.strip()

                sale_price_element = product.find_elements(By.CSS_SELECTOR, "div.product-card-price__old div.ft-line-through")
                sale_price = sale_price_element[0].text.strip() if sale_price_element else ''

                discount_element = product.find_elements(By.CSS_SELECTOR, "div.product-card-price__sale")
                discount = discount_element[0].text.strip() if discount_element else ''

                # Перевірка та обчислення знижки
                if sale_price and price:
                    try:
                        old_price = float(sale_price.replace(" грн", "").replace(",", ".").strip())
                        new_price = float(price.replace(" грн", "").replace(",", ".").strip())
                        calculated_discount = round((old_price - new_price) / old_price * 100)
                        print(f"[ЛОГ] Перерахований відсоток знижки: {calculated_discount}% (на сайті: {discount})")
                    except ValueError:
                        print(f"[ЛОГ] Помилка під час обчислення знижки для {product_name}")

                quotes.append([product_name, price, weight, sale_price, discount])
                print(f"[ЛОГ] Додано: {product_name}, Ціна: {price}")

            except (StaleElementReferenceException, TimeoutException, WebDriverException) as e:
                print(f"[ЛОГ] Помилка під час збору даних для {product_name}: {e}")

    except Exception as e:
        print(f"[ЛОГ] Загальна помилка збору даних: {e}")

    return quotes

# Функція для переходу на наступну сторінку
def go_to_next_page(driver):
    try:
        next_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.pagination-item--next-page"))
        )
        if "disabled" in next_button.get_attribute("class"):
            print("[ЛОГ] Це остання сторінка.")
            return False
        
        driver.execute_script("arguments[0].click();", next_button)
        print("[ЛОГ] Перехід на наступну сторінку.")
        return True
    except TimeoutException:
        print("[ЛОГ] Кнопка наступної сторінки не знайдена.")
        return False
    except WebDriverException as e:
        print(f"[ЛОГ] Помилка кліку: {e}")
        return False

# Основний код
base_url = 'https://silpo.ua/category/kava-v-zernakh-5111'
options = webdriver.ChromeOptions()
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
options.add_argument('--headless')
options.add_argument('--disable-cache')
options.add_argument('--incognito')

with webdriver.Chrome(options=options) as driver:
    driver.get(base_url)
    quotes = []
    page_number = 1

    while True:
        print(f"[ЛОГ] Завантаження сторінки {page_number}.")
        quotes = scrape_page(driver, quotes)
        time.sleep(random.uniform(3, 7))

        if quotes:
            header = ['Назва товару', 'Ціна товару', 'Вага товару', 'Стара ціна', 'Знижка']
            quotes.sort(key=lambda x: x[0])
            df = pd.DataFrame(quotes, columns=header)
            output_file = 'silpo_products.xlsx'
            df.to_excel(output_file, index=False, sheet_name='Products')
            print(f"Файл '{output_file}' оновлено після сторінки {page_number}.")

        if not go_to_next_page(driver):
            print("[ЛОГ] Завантаження завершено.")
            break
        page_number += 1

print(f"Файл '{output_file}' успішно створено!")
