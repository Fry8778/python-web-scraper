from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
import random

# Функція для збору даних з поточної сторінки  
def scrape_page(driver, quotes):
    try:
        # Очікування появи карток продуктів
        try:
            WebDriverWait(driver, 25).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".styles__StyledCard-sc-3jvmda-0.LSTlO"))
            )
        except TimeoutException:
            print("[ЛОГ] Час очікування вичерпано, картки продуктів не з'явились.")
            return quotes  # Якщо не вдалося знайти продукти за 50 секунд, виходимо з функції

        # Пошук всіх карток продуктів
        product_cards = driver.find_elements(By.CSS_SELECTOR, ".styles__StyledCard-sc-3jvmda-0.LSTlO")
        if not product_cards:
            print("[ЛОГ] Продукти не знайдені на сторінці. Спроба повторного пошуку.")
            time.sleep(2)
            product_cards = driver.find_elements(By.CSS_SELECTOR, ".styles__StyledCard-sc-3jvmda-0.LSTlO")
            if not product_cards:
                print("[ЛОГ] Продукти все ще не знайдені. Перехід до наступної сторінки.")
                return quotes

        # Обробка кожної картки продукту
        for product_card in product_cards:
            retry_count = 3
            try:
                # Знаходимо загальний блок з інформацією
                general_content = product_card.find_element(By.CSS_SELECTOR, ".general__content")

                # Назва продукту
                product_name_element = general_content.find_element(By.CSS_SELECTOR, ".prod__name")
                product_name = product_name_element.text.strip()

                # Перевірка на наявність товару через кнопку "Немає в наявності"
                out_of_stock_button = product_card.find_elements(By.CSS_SELECTOR, ".ant-btn.css-m54yah.ant-btn-disabled.ant-btn-block.add__remove__product.type-disabled")
                if out_of_stock_button:
                    print(f"[ЛОГ] Товар відсутній: {product_name}")
                    continue  # Пропускаємо товар, якщо він відсутній

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

                # Логіка запису в колонки
                if discount_amount:
                    # Якщо є знижка
                    special_price = price
                    regular_price = ""
                else:
                    # Якщо знижки немає
                    special_price = ""
                    regular_price = price

                # Логування зібраних даних
                print(f"[ЛОГ] Назва: {product_name}, Ціна: {price}, Знижка: {discount_amount}")

                # Додавання в таблицю
                quotes.append([ 
                    product_name,
                    f"{regular_price} грн" if regular_price else "",
                    f"{special_price} грн" if special_price else "",
                    f"{old_price} грн" if old_price else "",
                    f"{discount_amount} грн" if discount_amount else ""
                ])
                print(f"[ЛОГ] Додано: {product_name}")

            except StaleElementReferenceException:
                retry_count -= 1
                if retry_count == 0:
                    print(f"[ЛОГ] Пропущено через помилку: {product_name}")
            except Exception as e:
                print(f"[ЛОГ] Помилка при обробці продукту: {type(e).__name__}, {e}")
                continue

    except Exception as e:
        print(f"[ЛОГ] Загальна помилка: {type(e).__name__}, {e}")

    return quotes

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
    quotes = []

    print("[ЛОГ] Скролінг сторінки до кінця.")
    scroll_to_end(driver)

    # Збереження HTML сторінки для діагностики
    with open("page_source.html", "w", encoding="utf-8") as file:
        file.write(driver.page_source)

    print("[ЛОГ] Збирання товарів зі сторінки.")
    quotes = scrape_page(driver, quotes)

    if quotes:
        header = ['Назва товару', 'Ціна товару(грн)', 'Ціна товару з урахуванням знижки(грн)', 'Стара ціна товару(грн)', 'Знижка(грн)']
        quotes.sort(key=lambda x: x[0])
        df = pd.DataFrame(quotes, columns=header)
        df.to_excel('scraper_data_new.xlsx', index=False)
        print("[ЛОГ] Дані збережено у 'scraper_data_new.xlsx'")
    else:
        print("[ЛОГ] Дані не знайдено.")
