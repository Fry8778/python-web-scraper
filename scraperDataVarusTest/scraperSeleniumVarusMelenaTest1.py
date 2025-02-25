from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException  # 🔄 ЗМІНИ ВНЕСЕНО ТУТ
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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

# 🔄 ЗМІНИ ВНЕСЕНО ТУТ: Функція для безпечного отримання елемента
def get_element_safe(driver, locator, retries=3):
    for attempt in range(retries):
        try:
            return driver.find_element(*locator)
        except StaleElementReferenceException:
            print(f"⚡ Спроба {attempt + 1} - елемент застарів. Повторюю...")
            time.sleep(1)
    return None

# 🔄 ЗМІНИ ВНЕСЕНО ТУТ: Додано WebDriverWait для очікування елементів
def scrape_page(driver, quotes):
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".sf-product-card__wrapper"))
        )
        product_cards = driver.find_elements(By.CSS_SELECTOR, ".sf-product-card__wrapper")
        
        for product_card in product_cards:
            for attempt in range(3):  # 🔄 ЗМІНИ ВНЕСЕНО ТУТ: Спроби при StaleElementReferenceException
                try:
                    try:
                        out_of_stock_element = product_card.find_element(
                            By.CSS_SELECTOR, ".sf-product-card--out-of-stock-container")
                        print(f"[ЛОГ] Пропущено (відсутній на складі): {product_card.find_element(By.CSS_SELECTOR, '.sf-product-card__title').text.strip()}")
                        continue
                    except NoSuchElementException:
                        pass

                    product_name_element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".sf-product-card__title"))
                    )  # 🔄 ЗМІНИ ВНЕСЕНО ТУТ

                    product_name = product_name_element.text.strip()
                    
                    if is_duplicate(product_name):
                        print(f"[ЛОГ] Дублікат пропущено: {product_name}")
                        continue
                    
                    if not matches_filter(product_name):
                        print(f"[ЛОГ] Пропущено через невідповідність фільтру: {product_name}")
                        continue

                    # 🔄 ЗМІНИ ВНЕСЕНО ТУТ: Обробка StaleElementReferenceException при отриманні цін
                    def get_price(selector):
                        try:
                            return product_card.find_element(By.CSS_SELECTOR, selector).text.strip().replace("грн", "").replace(",", ".")
                        except NoSuchElementException:
                            return ""

                    special_price = get_price(".sf-price__special")
                    old_price = get_price(".sf-price__old")
                    regular_price = "" if special_price else get_price(".sf-price__regular")

                    discount_percentage = ""
                    try:
                        discount_elements = product_card.find_elements(By.CSS_SELECTOR, ".sf-product-card__badge_text")
                        for element in discount_elements:
                            text = element.text.strip()
                            if "%" in text:
                                discount_percentage = text.split()[0].replace("-", "").replace("%", "")
                                break
                    except NoSuchElementException:
                        pass

                    print(f"[ЛОГ] Ціна товару (регулярна): {regular_price} грн")
                    print(f"[ЛОГ] Ціна товару (зі знижкою): {special_price} грн")
                    print(f"[ЛОГ] Стара ціна товару: {old_price} грн")
                    print(f"[ЛОГ] Відсоток знижки: {discount_percentage}%")

                    quotes.append([
                        product_name,
                        f"{regular_price} грн" if regular_price else "",
                        f"{special_price} грн" if special_price else "",
                        f"{old_price} грн" if old_price else "",
                        f"{discount_percentage}%" if discount_percentage else ""
                    ])

                    print(f"[ЛОГ] Додано: {product_name}")
                    break  # Якщо успішно - вихід із циклу спроб

                except StaleElementReferenceException:
                    print("⚡ Елемент застарів під час обробки. Спроба знову...")
                    time.sleep(1)

    except TimeoutException:
        print("⚡ Час очікування елементів минув. Сторінка могла не завантажитися.")
    except Exception as e:
        print(f"[ЛОГ] Загальна помилка: {type(e).__name__}, {e}")

    return quotes

# Основний код
base_url = 'https://varus.ua/dnipro/kava-zernova~typ-kavy_melena'
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
            time.sleep(3)
            page_number += 1

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
        df.to_excel('scraper_selenium_Varus_melena_test1.xlsx', index=False)
        print("[ЛОГ] Дані збережено у 'scraper_selenium_Varus_melena_test1.xlsx'")
    else:
        print("[ЛОГ] Дані не знайдено.")
        
        
          # if quotes:
    #     df = pd.DataFrame(quotes, columns=[ 'Назва товару',
    #                                         'Ціна товару (грн)',
    #                                         'Ціна товару з урахуванням знижки (грн)',
    #                                         'Стара ціна товару(грн)',
    #                                         'Відсоток знижки (%)'
    #     ])
    #     df.to_excel('scraper_selenium_Varus_melena_test.xlsx', index=False)
    #     print("[ЛОГ] Дані збережено у 'scraper_selenium_Varus_melena_test.xlsx'")
    # else:
    #     print("[ЛОГ] Дані не знайдено.")

