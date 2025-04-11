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
    keywords = ["ЗЕР",
                "ЗЕРНО",
                "ЗЕРНОВА"
                "В ЗЕРНАХ",
                "КАВА ЗЕРНО",
                "КАВА В ЗЕРНАХ"]
    return any(keyword.lower() in product_name.lower() for keyword in keywords)

# Функція для збору даних з поточної сторінки
def scrape_page(driver, quotes):
    try:
        # Ожидаем появления элементов с классом js-product-miniature-wrapper
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".js-product-miniature-wrapper"))
        )
        product_cards = driver.find_elements(By.CSS_SELECTOR, ".js-product-miniature-wrapper")
        
        for product_card in product_cards:
            try:
                  # Фільтрація товарів, яких немає в наявності
                if "product_grey" in product_card.get_attribute("class"):
                    print("[ЛОГ] Пропущено (немає в наявності).")
                    continue
                
                # Назва продукту
                product_name_element = product_card.find_element(By.CSS_SELECTOR, ".h3.product-title a")
                product_name = product_name_element.text.strip()

                if not matches_filter(product_name):
                    print(f"[ЛОГ] Пропущено через невідповідність фільтру: {product_name}")
                    continue

                if is_duplicate(product_name):
                    print(f"[ЛОГ] Дублікат пропущено: {product_name}")
                    continue

                # Ціна товару
                try:
                    price_element = product_card.find_element(By.CSS_SELECTOR, ".product-price")
                    price = price_element.text.strip().replace("грн", "").replace(",", ".")
                except NoSuchElementException:
                    price = ""

                # Вага товару
                weight_element = product_card.find_element(By.CSS_SELECTOR, ".fasovka")
                weight_text = weight_element.text.strip().replace(" ", "").replace(",", "")
                # weight = weight_element.text.strip().replace(" ", "").replace(",", "").replace("г", "").replace("кг", "")
                
                # Конвертація ваги в грами
                if "кг" in weight_text:
                    weight = str(int(float(weight_text.replace("кг", "")) * 1000))  # Перетворення кг у г
                elif "г" in weight_text:
                    weight = weight_text.replace("г", "")
                else:
                    weight = weight_text  # Якщо формат невідомий, залишаємо як є
                
                # Старая цена
                old_price_elements = product_card.find_elements(By.CSS_SELECTOR, ".regular-price.text-muted")
                old_price = (
                    old_price_elements[0].text.strip().replace("грн", "").replace(",", ".")
                    if old_price_elements
                    else ""
                )

                # Скидка в процентах
                discount_elements = product_card.find_elements(By.CSS_SELECTOR, ".flag-discount-value")
                discount_percentage = (
                    discount_elements[0].text.strip().replace("-", "").replace("грн", "").replace(",", ".")
                    if discount_elements else ""
                )

                # Логика для записи цены
                special_price = price if old_price else ""
                regular_price = "" if old_price else price

                quotes.append([
                    product_name,
                    f"{regular_price}грн" if regular_price else "",
                    f"{weight} г",
                    f"{special_price}грн" if special_price else "",
                    f"{old_price}грн" if old_price else "",
                    f"{discount_percentage}грн" if discount_percentage else ""
                ])
                print(f"[ЛОГ] Додано: {product_name}")

            except Exception as e:
                print(f"[ЛОГ] Помилка при обробці продукту: {type(e).__name__}, {e}")
                continue

    except Exception as e:
        print(f"[ЛОГ] Загальна помилка: {type(e).__name__}, {e}")

    return quotes


# Функція для прокручування сторінки
def scroll_down(driver):
    scroll_pause_time = random.uniform(3, 7)
    current_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause_time)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == current_height:
            break
        current_height = new_height

# Основний код
base_url = 'https://fozzyshop.ua/dnipro/300507-kofe-v-zernakh'
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
            # Пошук всіх посилань пагінації
            pagination_links = driver.find_elements(By.CSS_SELECTOR, ".pagination li a")
            next_page_link = None

            for link in pagination_links:
                if link.text.strip() == str(page_number + 1):  # Пошук посилання на наступну сторінку
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
                  'Вага товару(г)',
                  'Ціна зі знижкою (грн)',
                  'Стара ціна (грн)',
                  'Знижка (грн)']
        quotes.sort(key=lambda x: x[0])
        df = pd.DataFrame(quotes, columns=header)
        df.to_excel('fozzy_kava_v_zernakh.xlsx', index=False)
        print("[ЛОГ] Дані збережено у 'fozzy_kava_v_zernakh.xlsx'")
    else:
        print("[ЛОГ] Дані не знайдено.")
