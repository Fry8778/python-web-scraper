import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd

# Перевірка на дублікати
unique_products = set()

def is_duplicate(product_name):
    if product_name in unique_products:
        return True
    unique_products.add(product_name)
    return False

# Функція збору даних зі сторінки
def scrape_page(driver, quotes):
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".sf-product-card__wrapper"))
        )
        product_cards = driver.find_elements(By.CSS_SELECTOR, ".sf-product-card__wrapper")

        for product_card in product_cards:
            try:
                # Пропуск товарів, яких немає в наявності
                if "sf-product-card--out-of-stock-container" in product_card.get_attribute("class"):
                    print(f"[ЛОГ] Пропущено (відсутній на складі): {product_card.find_element(By.CSS_SELECTOR, '.sf-product-card__title').text.strip()}")
                    continue

                # Назва товару
                product_name = product_card.find_element(By.CSS_SELECTOR, ".sf-product-card__title").text.strip()
                if is_duplicate(product_name):
                    continue

                # Отримання цін
                special_price = product_card.find_elements(By.CSS_SELECTOR, ".sf-price__special")
                regular_price = product_card.find_elements(By.CSS_SELECTOR, ".sf-price__regular")
                old_price = product_card.find_elements(By.CSS_SELECTOR, ".sf-price__old")
                discount = product_card.find_elements(By.CSS_SELECTOR, ".sf-product-card__badge_text")

                quotes.append([
                    product_name,
                    f"{regular_price[0].text.strip()} грн" if regular_price else "",
                    f"{special_price[0].text.strip()} грн" if special_price else "",
                    f"{old_price[0].text.strip()} грн" if old_price else "",
                    f"{discount[0].text.strip()}" if discount else ""
                ])

            except Exception as e:
                print(f"[ЛОГ] Помилка при обробці продукту: {type(e).__name__}, {e}")

    except TimeoutException:
        print("[ЛОГ] Не вдалося завантажити список товарів.")

    return quotes

# Основний код
base_url = 'https://varus.ua/kava-zernova~typ-kavy_u-zernakh'
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')

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
        df = pd.DataFrame(quotes, columns=[
            'Назва товару', 'Ціна товару (грн)', 'Ціна товару з урахуванням знижки (грн)',
            'Стара ціна товару(грн)', 'Відсоток знижки (%)'
        ])
        df.to_excel('data_varus6.xlsx', index=False)
        print("[ЛОГ] Дані збережено у 'data_varus6.xlsx'")
    else:
        print("[ЛОГ] Дані не знайдено.")
