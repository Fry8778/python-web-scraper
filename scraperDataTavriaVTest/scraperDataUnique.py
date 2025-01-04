from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
import random
import hashlib

# Функція для створення унікального хешу для продукту
def get_hash(product_name, price):
    return hashlib.md5(f"{product_name}_{price}".encode('utf-8')).hexdigest()

# Функція для збору даних з поточної сторінки
def scrape_page(driver, product_data):
    try:
        # Очікування появи карток продуктів
        try:
            WebDriverWait(driver, 25).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".styles__StyledCard-sc-3jvmda-0.LSTlO"))
            )
        except TimeoutException:
            print("[ЛОГ] Час очікування вичерпано, картки продуктів не з'явились.")
            return product_data

        # Пошук всіх карток продуктів
        product_cards = driver.find_elements(By.CSS_SELECTOR, ".styles__StyledCard-sc-3jvmda-0.LSTlO")
        if not product_cards:
            print("[ЛОГ] Продукти не знайдені на сторінці.")
            return product_data

        # Обробка кожної картки продукту
        for product_card in product_cards:
            retry_count = 3
            try:
                # Знаходимо загальний блок з інформацією
                general_content = product_card.find_element(By.CSS_SELECTOR, ".general__content")

                # Отримання повної назви продукту
                product_name_element = general_content.find_element(By.CSS_SELECTOR, ".prod__name")
                product_name = product_name_element.get_attribute("title").strip() if product_name_element.get_attribute("title") else product_name_element.text.strip()

                # Перевірка на наявність товару через кнопку "Немає в наявності"
                out_of_stock_button = product_card.find_elements(By.CSS_SELECTOR, ".ant-btn.css-m54yah.ant-btn-disabled.ant-btn-block.add__remove__product.type-disabled")
                if out_of_stock_button:
                    print(f"[ЛОГ] Товар відсутній: {product_name}")
                    continue

                # Ціна товару
                price_element = general_content.find_element(By.CSS_SELECTOR, ".base__price")
                price = price_element.text.strip().replace("₴", "").replace(",", ".") if price_element else ""

                # Стара ціна
                old_price_element = general_content.find_elements(By.CSS_SELECTOR, ".prod-crossed-out__price__old")
                old_price = (
                    old_price_element[0].text.strip().replace("₴", "").replace(",", ".").replace("(", "").replace(")", "")
                    if old_price_element
                    else ""
                )

                # Знижка
                discount_text_element = general_content.find_elements(By.CSS_SELECTOR, ".prod-crossed-out__price__special-off")
                discount_text = discount_text_element[0].text.strip() if discount_text_element else ""
                discount_amount = discount_text.replace("Економія", "").replace("₴", "").replace(",", ".").strip() if discount_text else ""

                # Логіка запису унікальних продуктів
                product_hash = get_hash(product_name, price)
                if product_hash not in product_data:
                    product_data[product_hash] = {
                        'name': product_name,
                        'price': price,
                        'special_price': price if discount_amount else "",
                        'old_price': old_price,
                        'discount': discount_amount
                    }
                    print(f"[ЛОГ] Додано: {product_name}")
                else:
                    print(f"[ЛОГ] Продукт {product_name} вже існує у списку.")

            except StaleElementReferenceException:
                retry_count -= 1
                if retry_count == 0:
                    print(f"[ЛОГ] Пропущено через помилку: {product_name}")
            except Exception as e:
                print(f"[ЛОГ] Помилка при обробці продукту: {type(e).__name__}, {e}")
                continue

    except Exception as e:
        print(f"[ЛОГ] Загальна помилка: {type(e).__name__}, {e}")

    return product_data

# Функція для прокручування сторінки до кінця
def scroll_to_end(driver):
    scroll_pause_time = random.uniform(5, 10)
    current_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause_time)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == current_height:
            break
        current_height = new_height

# Основний код
base_url = 'https://www.tavriav.ua/ca/%D1%87%D0%B0%D1%97-%D0%BA%D0%B0%D0%B2%D0%B0-%D1%82%D0%B0-%D0%BA%D0%B0%D0%BA%D0%B0%D0%BE/%D0%BA%D0%B0%D0%B2%D0%BE%D0%B2%D1%96-%D0%BD%D0%B0%D0%BF%D0%BE%D1%97/9829/9830'
options = webdriver.ChromeOptions()
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

with webdriver.Chrome(options=options) as driver:
    driver.get(base_url)
    product_data = {}

    print("[ЛОГ] Скролінг сторінки до кінця.")
    scroll_to_end(driver)

    print("[ЛОГ] Збирання товарів зі сторінки.")
    product_data = scrape_page(driver, product_data)

    if product_data:
        header = ['ID товару', 'Назва товару', 'Ціна товару(грн)', 'Ціна товару з урахуванням знижки(грн)', 'Стара ціна товару(грн)', 'Знижка(грн)']
        data_rows = [
            [product_id, 
             details['name'], 
             f"{details['price']} грн" if details['price'] else "",
             f"{details['special_price']} грн" if details['special_price'] else "",
             f"{details['old_price']} грн" if details['old_price'] else "",
             f"{details['discount']} грн" if details['discount'] else ""]
            for product_id, details in product_data.items()
        ]

        df = pd.DataFrame(data_rows, columns=header)
        df.to_excel('scraper_data_unique.xlsx', index=False)
        print("[ЛОГ] Дані збережено у 'scraper_data_unique.xlsx'")
    else:
        print("[ЛОГ] Дані не знайдено.")
