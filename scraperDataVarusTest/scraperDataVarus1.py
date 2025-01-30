from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
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

# Перевірка чи назва продукту відповідає фільтру
def matches_filter(product_name):    
    keywords = ["В ЗЕРНАХ", "ЗЕР", "ЗЕРНО", "ЗЕРНОВА"]
    return any(keyword.lower() in product_name.lower() for keyword in keywords)

# Функція для збору даних з поточної сторінки
def scrape_page(driver, quotes):
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".sf-product-card__wrapper"))
        )
        product_cards = driver.find_elements(By.CSS_SELECTOR, ".sf-product-card__wrapper")
        
        for product_card in product_cards:
            try:
                # Назва продукту
                product_name_element = product_card.find_element(By.CSS_SELECTOR, ".sf-product-card__title")
                product_name = product_name_element.text.strip()

                if not matches_filter(product_name):
                    print(f"[ЛОГ] Пропущено через невідповідність фільтру: {product_name}")
                    continue

                if is_duplicate(product_name):
                    print(f"[ЛОГ] Дублікат пропущено: {product_name}")
                    continue

                # Ціна товару                
                price_element = product_card.find_element(By.CSS_SELECTOR, ".sf-price__regular")
                price = price_element.text.strip().replace("грн", "").replace(",", ".") if price_element else ""
               
                
                # Стара ціна
                old_price_element = product_card.find_element(By.CSS_SELECTOR, ".sf-price__old")
                old_price = (
                    old_price_element[0].text.strip().replace("грн.", "").replace(",", ".")
                    if old_price_element
                    else ""
                )
                
                # Знижка в процентах
                discount_element = product_card.find_element(By.CSS_SELECTOR, ".sf-product-card__badge_text")
                discount_percentage = (
                    discount_element[0].text.strip().replace("-", "").replace("%", "") if discount_element else ""
                )
                               
                # Логіка запису в колонки
                special_price = price if old_price else ""
                regular_price = "" if old_price else price

                quotes.append([
                    product_name,
                    f"{regular_price} грн" if regular_price else "",
                    f"{special_price} грн" if special_price else "",
                    f"{old_price} грн" if old_price else "",
                    f"{discount_percentage} %" if discount_percentage else ""
                ])
                print(f"[ЛОГ] Додано: {product_name}")

            except Exception as e:
                print(f"[ЛОГ] Помилка при обробці продукту: {type(e).__name__}, {e}")
                continue

    except Exception as e:
        print(f"[ЛОГ] Загальна помилка: {type(e).__name__}, {e}")

    return quotes

# Основний код
base_url = 'https://varus.ua/kava-zernova'
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

with webdriver.Chrome(options=options) as driver:
    driver.get(base_url)
    quotes = []
    page_number = 1

    while True:
        print(f"[ЛОГ] Обробляється сторінка {page_number}.")
        quotes = scrape_page(driver, quotes)

        try:
            # Пошук посилання на наступну сторінку
            next_page_link = None
            pagination_links = driver.find_elements(By.CSS_SELECTOR, ".sf-pagination__item")
            
            for link in pagination_links:
                if link.text.strip() == str(page_number + 1):
                    next_page_link = link.get_attribute("href")
                    break

            if not next_page_link:
                print("[ЛОГ] Наступної сторінки немає. Завершення.")
                break

            print(f"[ЛОГ] Переходжу до сторінки {page_number + 1}: {next_page_link}")
            driver.get(next_page_link)
            time.sleep(3)  # Коротка пауза для завантаження сторінки
            page_number += 1

        except NoSuchElementException:
            print("[ЛОГ] Наступної сторінки не знайдено. Завершення.")
            break

    if quotes:
        header = ['Назва товару', 'Ціна товару (грн)', 'Ціна зі знижкою (грн)', 'Стара ціна (грн)', 'Знижка (%)']
        quotes.sort(key=lambda x: x[0])
        df = pd.DataFrame(quotes, columns=header)
        df.to_excel('data_varus1.xlsx', index=False)
        print("[ЛОГ] Дані збережено у 'data_varus1.xlsx'")
    else:
        print("[ЛОГ] Дані не знайдено.")
