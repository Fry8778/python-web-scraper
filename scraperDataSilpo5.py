from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
import random

def scrape_page(driver, quotes):
    products = driver.find_elements(By.CLASS_NAME, "product-card")
    for product in products:
        try:
            title = product.find_element(By.CLASS_NAME, "product-card__title").text.strip()
            price = product.find_element(By.CLASS_NAME, "ft-whitespace-nowrap.ft-text-22.ft-font-bold").text.strip()
            weight = product.find_element(By.CLASS_NAME, "ft-typo-14-semibold").text.strip()

            quotes.append({
                'Назва товару': title,
                'Ціна товару': price,
                'Вага товару': weight
            })
        except NoSuchElementException:
            continue

def go_to_next_page(driver):
    try:
        next_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.pagination-item:not(.pagination-item--current)"))
        )

        # Імітація прокручування сторінки
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # Час очікування

        # Імітація кліку по кнопці
        next_button.click()
        time.sleep(random.uniform(5, 10))  # Випадкова пауза між сторінками
        return True
    except (TimeoutException, WebDriverException) as e:
        print(f"Помилка при переході на наступну сторінку: {e}")
        return False

# Налаштування браузера
base_url = 'https://silpo.ua/category/kava-v-zernakh-5111'
options = webdriver.ChromeOptions()
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-webgl')
options.add_argument('--disable-extensions')
options.add_argument('--disable-infobars')
options.add_argument('--disable-features=VizDisplayCompositor')

# Запуск браузера
with webdriver.Chrome(options=options) as driver:
    driver.get(base_url)
    quotes = []

    while True:
        scrape_page(driver, quotes)

        # Перехід на наступну сторінку
        if not go_to_next_page(driver):
            break

# Збереження даних у файл Excel
output_file = 'silpo_products.xlsx'
df = pd.DataFrame(quotes)
df.to_excel(output_file, index=False, sheet_name='Products')
print(f"Файл '{output_file}' успішно створено!")
