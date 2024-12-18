from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
import random

unique_products = set()

def is_duplicate(product_name):
    if product_name in unique_products:
        return True
    unique_products.add(product_name)
    return False

def scrape_page(driver, quotes):
    try:
        products = driver.find_elements(By.CLASS_NAME, "product-card")
        if not products:
            print("[ЛОГ] Продукти не знайдені на сторінці.")

        for product in products:
            try:
                title = product.find_element(By.CLASS_NAME, "product-card__title").text.strip()
                price = product.find_element(By.CLASS_NAME, "ft-whitespace-nowrap.ft-text-22.ft-font-bold").text.strip()
                weight = product.find_element(By.CLASS_NAME, "ft-typo-14-semibold").text.strip()

                if is_duplicate(title):
                    print(f"[ЛОГ] Знайдено дублікат: {title}")
                    continue

                quotes.append({
                    'Назва товару': title,
                    'Ціна товару': price,
                    'Вага товару': weight
                })
            except NoSuchElementException:
                print("[ЛОГ] Деякі елементи товару відсутні.")
                continue
    except Exception as e:
        print(f"[ЛОГ] Помилка збору даних зі сторінки: {e}")

previous_url = ""

def go_to_next_page(driver):
    global previous_url
    try:
        for _ in range(5):
            driver.execute_script("window.scrollBy(0, 300);")
            time.sleep(1)

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
        scrape_page(driver, quotes)
        time.sleep(random.uniform(3, 7))

        if not go_to_next_page(driver):
            print("[ЛОГ] Завантаження завершено.")
            break
        page_number += 1

output_file = 'silpo_products.xlsx'
df = pd.DataFrame(quotes)
df.to_excel(output_file, index=False, sheet_name='Products')
print(f"Файл '{output_file}' успішно створено!")
