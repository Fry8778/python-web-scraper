from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
import random

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

                # Отримання назви продукту
                product_name_element = general_content.find_element(By.CSS_SELECTOR, ".prod__name")
                product_name = product_name_element.text.strip()

                # Перевірка на наявність товару через кнопку "Немає в наявності"
                out_of_stock_button = product_card.find_elements(By.CSS_SELECTOR, ".ant-btn.css-m54yah.ant-btn-disabled.ant-btn-block.add__remove__product.type-disabled")
                if out_of_stock_button:
                    print(f"[ЛОГ] Товар відсутній: {product_name}")
                    continue

                # Знаходимо основну ціну
                try:
                    price_element = general_content.find_element(By.CSS_SELECTOR, ".CardBasePrice__CardBasePriceStyles-sc-1dlx87w-0.bhSKFL")
                    price = price_element.text.strip()
                except Exception:
                    price_element = general_content.find_element(By.CSS_SELECTOR, ".base__price")
                    price = price_element.text.strip() if price_element else ""

                # Знаходимо стару ціну
                old_price_element = general_content.find_elements(By.CSS_SELECTOR, ".prod-crossed-out__price__old")
                old_price = (
                    old_price_element[0].text.strip() if old_price_element else ""
                )

                # Знаходимо економію
                discount_text_element = general_content.find_elements(By.CSS_SELECTOR, ".prod-crossed-out__price__special-off")
                discount_text = discount_text_element[0].text.strip() if discount_text_element else ""

                # Очищення даних від небажаних символів
                price = price.replace("₴", "").replace(",", ".").replace("(", "").replace(")", "").strip()
                old_price = old_price.replace("₴", "").replace(",", ".").replace("(", "").replace(")", "").strip()
                discount_amount = discount_text.replace("Економія", "").replace("₴", "").replace(",", ".").replace("(", "").replace(")", "").strip()

                # Логування зібраних даних
                print(f"[ЛОГ] Назва: {product_name}, Ціна: {price}, Стара ціна: {old_price}, Економія: {discount_amount}")

                # Додавання в таблицю
                product_data.append([
                    product_name,
                    f"{price} грн" if price else "",
                    f"{old_price} грн" if old_price else "",
                    f"{discount_amount} грн" if discount_amount else ""
                ])

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
base_url = 'https://www.tavriav.ua/ca/%D1%87%D0%B0%D0%B8-%D0%BA%D0%B0%D0%B2%D0%B0-%D1%82%D0%B0-%D0%BA%D0%B0%D0%BA%D0%B0%D0%BE/%D0%BA%D0%B0%D0%B2%D0%BE%D0%B2%D1%96-%D0%BD%D0%B0%D0%BF%D0%BE%D1%96/9829/9830'
options = webdriver.ChromeOptions()
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

with webdriver.Chrome(options=options) as driver:
    driver.get(base_url)
    product_data = []

    print("[ЛОГ] Скролінг сторінки до кінця.")
    scroll_to_end(driver)

    print("[ЛОГ] Збирання товарів зі сторінки.")
    product_data = scrape_page(driver, product_data)

    if product_data:
        header = ['Назва товару', 'Ціна товару(грн)', 'Стара ціна товару(грн)', 'Знижка(грн)']
        product_data.sort(key=lambda x: x[0])
        df = pd.DataFrame(product_data, columns=header)
        df.to_excel('scraper_data_with_JS_code.xlsx', index=False)
        print("[ЛОГ] Дані збережено у 'scraper_data_with_JS_code.xlsx'")
    else:
        print("[ЛОГ] Дані не знайдено.")
