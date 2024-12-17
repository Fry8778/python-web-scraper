from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time

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

# Налаштування браузера
base_url = 'https://silpo.ua/category/kava-v-zernakh-5111'
options = webdriver.ChromeOptions()
options.add_argument('--headless')  # Запуск без вікна браузера (за бажанням)
# options.add_argument('--headless') == False  # Відкриття браузера у видимому режимі
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument('--disable-webgl')
options.add_argument('--disable-webgpu')
options.add_argument('--disable-software-rasterizer')
options.add_argument('--disable-accelerated-2d-canvas')
options.add_argument('--use-angle=gl')
options.add_argument('--disable-gpu-compositing')
options.add_argument('--disable-extensions')
options.add_argument('--disable-infobars')
options.add_argument('--disable-features=VizDisplayCompositor')

# Запуск браузера
with webdriver.Chrome(options=options) as driver:
    driver.get(base_url)
    quotes = []

    while True:
        scrape_page(driver, quotes)
        try:
            # Очікування кнопки "Наступна сторінка"
            next_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a.pagination-item.pagination-item--next"))
            )
            ActionChains(driver).move_to_element(next_button).click().perform()
            time.sleep(2)  # Час очікування завантаження сторінки
        except TimeoutException:
            break

# Збереження даних у файл Excel
output_file = 'silpo_products.xlsx'
df = pd.DataFrame(quotes)
df.to_excel(output_file, index=False, sheet_name='Products')
print(f"Файл '{output_file}' успішно створено!")
