from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urljoin
import pandas as pd
import time
import re

# Перевірка на дублікати
unique_products = set()

def is_duplicate(product_name):
    if product_name in unique_products:
        return True
    unique_products.add(product_name)
    return False

def matches_filter(product_name):
    keywords = ["МЕЛЕНА", "МЕЛ"]
    cleaned_name = re.sub(r"[^\w\s]", "", product_name)
    return any(keyword.lower() in cleaned_name.lower() for keyword in keywords)

def wait_for_full_load(driver, timeout=30):
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script('return document.readyState') == 'complete'
    )

def scroll_to_bottom(driver):
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def scrape_page(driver, quotes):
    retries = 3
    for attempt in range(retries):
        try:
            wait_for_full_load(driver)
            scroll_to_bottom(driver)
            WebDriverWait(driver, 30).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".sf-product-card__wrapper"))
            )
            product_cards = driver.find_elements(By.CSS_SELECTOR, ".sf-product-card__wrapper")
            
            for product_card in product_cards:
                try:
                    try:
                        product_card.find_element(By.CSS_SELECTOR, ".sf-product-card--out-of-stock-container")
                        print(f"[ЛОГ] Пропущено (відсутній на складі): {product_card.find_element(By.CSS_SELECTOR, '.sf-product-card__title').text.strip()}")
                        continue
                    except NoSuchElementException:
                        pass

                    product_name = product_card.find_element(By.CSS_SELECTOR, ".sf-product-card__title").text.strip()
                    if is_duplicate(product_name):
                        print(f"[ЛОГ] Дублікат пропущено: {product_name}")
                        continue
                    if not matches_filter(product_name):
                        print(f"[ЛОГ] Пропущено через невідповідність фільтру: {product_name}")
                        continue

                    special_price = product_card.find_element(By.CSS_SELECTOR, ".sf-price__special").text.strip().replace("грн", "").replace(",", ".") if product_card.find_elements(By.CSS_SELECTOR, ".sf-price__special") else ""
                    old_price = product_card.find_element(By.CSS_SELECTOR, ".sf-price__old").text.strip().replace("грн", "").replace(",", ".") if product_card.find_elements(By.CSS_SELECTOR, ".sf-price__old") else ""
                    regular_price = product_card.find_element(By.CSS_SELECTOR, ".sf-price__regular").text.strip().replace("грн", "").replace(",", ".") if not special_price and product_card.find_elements(By.CSS_SELECTOR, ".sf-price__regular") else ""

                    discount_percentage = ""
                    for element in product_card.find_elements(By.CSS_SELECTOR, ".sf-product-card__badge_text"):
                        text = element.text.strip()
                        if "%" in text:
                            discount_percentage = text.split()[0].replace("-", "").replace("%", "")
                            break

                    print(f"[ЛОГ] Додано: {product_name}")
                    quotes.append([
                        product_name,
                        f"{regular_price} грн" if regular_price else "",
                        f"{special_price} грн" if special_price else "",
                        f"{old_price} грн" if old_price else "",
                        f"{discount_percentage}%" if discount_percentage else ""
                    ])

                except Exception as e:
                    print(f"[ЛОГ] Помилка при обробці продукту: {type(e).__name__}, {e}")
                    continue
            return quotes
        except TimeoutException as e:
            print(f"[ЛОГ] Спроба {attempt + 1}/{retries}: TimeoutException. Повторна спроба...")
            if attempt == retries - 1:
                print("[ЛОГ] Максимальна кількість спроб вичерпана. Перехід до наступної сторінки.")
                return quotes

def main():
    base_url = 'https://varus.ua'
    category_url = '/dnipro/kava-zernova~typ-kavy_melena'

    options = webdriver.ChromeOptions()
    options.add_argument('--enable-unsafe-swiftshader')
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    with webdriver.Chrome(options=options) as driver:
        driver.get(urljoin(base_url, category_url))
        quotes = []
        page_number = 1

        while True:
            print(f"[ЛОГ] Обробляється сторінка {page_number}.")
            quotes = scrape_page(driver, quotes)

            try:
                next_button = driver.find_elements(By.CSS_SELECTOR, ".sf-pagination__item--next:not(.sf-pagination__item--next--disable)")
                if next_button:
                    next_page_link = next_button[0].find_element(By.TAG_NAME, 'a').get_attribute("href")
                    if next_page_link:
                        print(f"[ЛОГ] Переходжу до сторінки {page_number + 1}: {next_page_link}")
                        driver.get(next_page_link)
                        page_number += 1
                    else:
                        print("[ЛОГ] Посилання на наступну сторінку відсутнє. Завершення.")
                        break
                else:
                    print("[ЛОГ] Наступної сторінки немає. Завершення.")
                    break

            except NoSuchElementException:
                print("[ЛОГ] Наступної сторінки не знайдено. Завершення.")
                break

        if quotes:
            header = ['Назва товару',
                      'Ціна товару (грн)',
                      'Ціна товару з урахуванням знижки (грн)',
                      'Стара ціна товару(грн)',
                      'Відсоток знижки (%)']
            quotes.sort(key=lambda x: x[0])
            df = pd.DataFrame(quotes, columns=header)
            df.to_excel('scraper_selenium_Varus_melena_test3.xlsx', index=False)
            print("[ЛОГ] Дані збережено у 'scraper_selenium_Varus_melena_test3.xlsx'")
        else:
            print("[ЛОГ] Дані не знайдено.")

if __name__ == "__main__":
    main()
