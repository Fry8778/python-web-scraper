from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
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

# def matches_filter(product_name):
#     keywords = ["В ЗЕРНАХ", "ЗЕР", "ЗЕРНО", "ЗЕРНОВА"]
#     return any(keyword.lower() in product_name.lower() for keyword in keywords)


def matches_filter(product_name):
    keywords = ["В ЗЕРНАХ", "ЗЕР", "ЗЕРНО", "ЗЕРНОВА"]
    cleaned_name = re.sub(r"[^\w\s]", "", product_name)  # Видаляє все, крім літер та пробілів
    return any(keyword.lower() in cleaned_name.lower() for keyword in keywords)

# Функція для збору даних з поточної сторінки
def scrape_page(driver, quotes):
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".sf-product-card__wrapper"))
        )
        product_cards = driver.find_elements(By.CSS_SELECTOR, ".sf-product-card__wrapper")
        
        for product_card in product_cards:
            try:
                # Перевірка наявності товару
                try:                    
                    out_of_stock_element = product_card.find_element(By.CSS_SELECTOR, ".sf-product-card--out-of-stock-container")
                    # out_of_stock_element = product_card.find_element(By.CSS_SELECTOR, ".sf-product-card__out-of-stock--label")
                    print(f"[ЛОГ] Пропущено (відсутній на складі): {product_card.find_element(By.CSS_SELECTOR, '.sf-product-card__title').text.strip()}")
                    continue
                except NoSuchElementException:
                    pass
                
                # if "sf-product-card--out-of-stock-container" in product_card.get_attribute("class"):
                #     print(f"[ЛОГ] Пропущено (відсутній на складі): {product_card.find_element(By.CSS_SELECTOR, '.sf-product-card__title').text.strip()}")
                #     continue
                            
                # Назва продукту
                product_name_element = product_card.find_element(By.CSS_SELECTOR, ".sf-product-card__title")
                product_name = product_name_element.text.strip()
                
                if is_duplicate(product_name):
                    print(f"[ЛОГ] Дублікат пропущено: {product_name}")
                    continue
                
                if not matches_filter(product_name):
                    print(f"[ЛОГ] Пропущено через невідповідність фільтру: {product_name}")
                    continue
                
                # Ціна товару
                special_price = ""
                try:
                    price_element = product_card.find_element(By.CSS_SELECTOR, ".sf-price__special")
                    special_price = price_element.text.strip().replace("грн", "").replace(",", ".")
                except NoSuchElementException:
                    pass

                # Стара ціна
                old_price = ""
                try:
                    old_price_element = product_card.find_element(By.CSS_SELECTOR, ".sf-price__old")
                    old_price = old_price_element.text.strip().replace("грн", "").replace(",", ".")
                except NoSuchElementException:
                    pass
                
                # Якщо немає знижки, шукаємо звичайну ціну
                regular_price = ""
                if not special_price:
                    try:
                        regular_price_element = product_card.find_element(By.CSS_SELECTOR, ".sf-price__regular")
                        regular_price = regular_price_element.text.strip().replace("грн", "").replace(",", ".")
                    except NoSuchElementException:
                        pass
                
                # Знижка в процентах
                discount_percentage = ""
                try:
                    discount_elements = product_card.find_elements(By.CSS_SELECTOR, ".sf-product-card__badge_text")
                    for element in discount_elements:
                        text = element.text.strip()
                        if "%" in text:  # Фільтруємо лише ті, що містять відсотки
                            discount_percentage = text.split()[0].replace("-", "").replace("%", "")
                            break  # Беремо лише перше знайдене значення
                except NoSuchElementException:
                    pass
                    
                # Логування цін перед додаванням у список
                print(f"[ЛОГ] Ціна товару (регулярна): {regular_price} грн")
                print(f"[ЛОГ] Ціна товару (зі знижкою): {special_price} грн")
                print(f"[ЛОГ] Стара ціна товару: {old_price} грн")
                print(f"[ЛОГ] Відсоток знижки: {discount_percentage}%")

                quotes.append([product_name,
                    f"{regular_price} грн" if regular_price else "",
                    f"{special_price} грн" if special_price else "",
                    f"{old_price} грн" if old_price else "",
                    f"{discount_percentage}%" if discount_percentage else ""])

                print(f"[ЛОГ] Додано: {product_name}")

            except Exception as e:
                print(f"[ЛОГ] Помилка при обробці продукту: {type(e).__name__}, {e}")
                continue

    except Exception as e:
        print(f"[ЛОГ] Загальна помилка: {type(e).__name__}, {e}")

    return quotes

# Основний код
base_url = 'https://varus.ua/kava-zernova~typ-kavy_u-zernakh'
# base_url = 'https://varus.ua/dnipro/kava-zernova~typ-kavy_u-zernakh'
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
        header = ['Назва товару',
                  'Ціна товару (грн)',
                  'Ціна товару з урахуванням знижки (грн)',
                  'Стара ціна товару(грн)',
                  'Відсоток знижки (%)']
        quotes.sort(key=lambda x: x[0])
        df = pd.DataFrame(quotes, columns=header)
        df.to_excel('scraper_selenium_Varus_v_zernakh_test.xlsx', index=False)
        print("[ЛОГ] Дані збережено у 'scraper_selenium_Varus_v_zernakh_test.xlsx'")
    else:
        print("[ЛОГ] Дані не знайдено.")
    
    # if quotes:
    #     df = pd.DataFrame(quotes, columns=[ 'Назва товару',
    #                                         'Ціна товару (грн)',
    #                                         'Ціна товару з урахуванням знижки (грн)',
    #                                         'Стара ціна товару(грн)',
    #                                         'Відсоток знижки (%)'
    #     ])
    #     df.to_excel('scraper_selenium_Varus_v_zernakh_test.xlsx', index=False)
    #     print("[ЛОГ] Дані збережено у 'scraper_selenium_Varus_v_zernakh_test.xlsx'")
    # else:
    #     print("[ЛОГ] Дані не знайдено.")

