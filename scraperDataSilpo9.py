from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException, WebDriverException
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
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "product-card__body"))
        )
        products = driver.find_elements(By.CLASS_NAME, "product-card__body")
        
        if not products:
            print("[ЛОГ] Продукти не знайдені на сторінці.")

        for index, _ in enumerate(products):
            try:
                product = driver.find_elements(By.CLASS_NAME, "product-card__body")[index]
                product_name_element = product.find_element(By.CLASS_NAME, "product-card__title")
                product_name = product_name_element.text.strip()

                if is_duplicate(product_name):
                    continue

                price = product.find_element(By.CLASS_NAME, "ft-whitespace-nowrap.ft-text-22.ft-font-bold").text.strip()
                weight = product.find_element(By.CLASS_NAME, "ft-typo-14-semibold").text.strip()
                
                special_price_elements = product.find_elements(By.CLASS_NAME, "ft-whitespace-nowrap.ft-text-22.ft-font-bold")
                sale_price_elements = product.find_elements(By.CLASS_NAME, "ft-line-through.ft-text-black-87.ft-typo-14-regular.xl\\:ft-typo")
                discount_elements = product.find_elements(By.CLASS_NAME, "product-card-price__sale")

                special_price = special_price_elements[0].text.strip() if special_price_elements else ''
                sale_price = sale_price_elements[0].text.strip() if sale_price_elements else ''
                discount = discount_elements[0].text.strip() if discount_elements else ''

                quotes.append([product_name, price, weight, special_price, sale_price, discount])
                print(f"[ЛОГ] Додано: {product_name}, Ціна: {price}")

            except (NoSuchElementException, StaleElementReferenceException) as e:
                print(f"[ЛОГ] Помилка з елементом: {e}")
                continue

    except Exception as e:
        print(f"[ЛОГ] Загальна помилка збору даних: {e}")

    return quotes

# Функція для переходу на наступну сторінку
previous_url = ""

def go_to_next_page(driver):
    global previous_url
    try:
        for _ in range(10):
            driver.execute_script("window.scrollBy(0, 500);")
            time.sleep(0.5)

        next_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.pagination-item.pagination-item--next-page"))
        )

        driver.execute_script("arguments[0].click();", next_button)
        WebDriverWait(driver, 10).until(EC.url_changes(previous_url))
        previous_url = driver.current_url
        print("[ЛОГ] Перехід на наступну сторінку.")
        return True
    except TimeoutException:
        print("[ЛОГ] Кнопка наступної сторінки не знайдена.")
        return False
    except WebDriverException as e:
        print(f"[ЛОГ] Помилка при кліку на кнопку: {e}")
        return False

# Основний код
base_url = 'https://silpo.ua/category/kava-v-zernakh-5111'
options = webdriver.ChromeOptions()
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-webgl')
options.add_argument('--disable-extensions')

with webdriver.Chrome(options=options) as driver:
    driver.get(base_url)
    quotes = []
    page_number = 1

    while True:
        print(f"[ЛОГ] Завантаження сторінки {page_number}.")
        quotes = scrape_page(driver, quotes)
        time.sleep(random.uniform(3, 7))

        if not go_to_next_page(driver):
            print("[ЛОГ] Завантаження завершено.")
            break
        page_number += 1

# Додаємо заголовок перед записом в Excel лише один раз
header = ['Назва товару', 'Ціна товару', 'Вага товару', 'Ціна зі знижкою', 'Стара ціна', 'Процент знижки(%)']

# Сортуємо дані за назвою товару
quotes.sort(key=lambda x: x[0])

# Додаємо заголовок і створюємо DataFrame
df = pd.DataFrame(quotes, columns=header)

# Збереження результатів у файл Excel
output_file = 'silpo_products.xlsx'
df.to_excel(output_file, index=False, sheet_name='Products')
print(f"Файл '{output_file}' успішно створено!")
