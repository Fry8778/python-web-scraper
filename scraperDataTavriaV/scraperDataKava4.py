from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException, WebDriverException
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

# Функція для збору даних з поточної сторінки
def scrape_page(driver, quotes):
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".general__content"))
        )
        products = driver.find_elements(By.CSS_SELECTOR, ".general__content")

        if not products:
            print("[ЛОГ] Продукти не знайдені на сторінці.")
            return quotes

        for product in products:
            retry_count = 3  # Число спроб
            while retry_count > 0:
                try:
                    # Назва продукту
                    product_name_element = WebDriverWait(product, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".prod__name"))
                    )
                    product_name = product_name_element.text.strip()

                    if is_duplicate(product_name):
                        break

                    # Ціна
                    price_element = product.find_element(By.CSS_SELECTOR, ".base__price")
                    price = price_element.text.strip().replace("₴", "").replace(",", ".") if price_element else ""

                    # Стара ціна
                    old_price_element = product.find_elements(By.CSS_SELECTOR, ".prod-crossed-out__price__old")
                    old_price = old_price_element[0].text.strip().replace("₴", "").replace(",", ".") if old_price_element else ""

                    # Знижка (у вигляді "Ціна товару з урахуванням знижки")
                    discount_text_element = product.find_elements(By.CSS_SELECTOR, ".prod-crossed-out__price__special-off")
                    discount_text = discount_text_element[0].text.strip() if discount_text_element else ""
                    discount_amount = discount_text.replace("Ціна товару з урахуванням знижки", "").replace("₴", "").replace(",", ".").strip() if discount_text else ""

                    # Логіка обчислення ціни зі знижкою та відсотка знижки
                    special_price = float(price) if price else ""
                    discount_percentage = ""
                    if old_price and price:
                        try:
                            original_price = float(old_price)
                            special_price = float(price)
                            discount_percentage = round(((original_price - special_price) / original_price) * 100, 2)
                        except ValueError:
                            discount_percentage = ""

                    # Додавання в таблицю
                    quotes.append([
                        product_name,
                        f"{special_price:.2f} грн" if special_price else "",
                        f"{old_price} грн" if old_price else "",
                        f"{discount_amount} грн" if discount_amount else "",
                        f"{discount_percentage}%" if discount_percentage else ""
                    ])
                    print(f"[ЛОГ] Додано: {product_name}, Ціна: {special_price:.2f} грн, Відсоток знижки: {discount_percentage}%")
                    break

                except StaleElementReferenceException as e:
                    retry_count -= 1
                    print(f"[ЛОГ] Сталася помилка з елементом, залишилося спроб: {retry_count}. Помилка: {e}")
                    if retry_count == 0:
                        print(f"[ЛОГ] Не вдалося отримати елемент після кількох спроб: {product_name}")

                except TimeoutException as e:
                    print(f"[ЛОГ] Час очікування сплив: {e}")
                    break

                except Exception as e:
                    print(f"[ЛОГ] Загальна помилка при зборі даних: {type(e).__name__}, {e}")

    except Exception as e:
        print(f"[ЛОГ] Загальна помилка збору даних: {type(e).__name__}, {e}")

    return quotes

# Функція для прокручування сторінки вниз
def scroll_down(driver):
    scroll_pause_time = random.uniform(1.5, 3.5)  # Випадковий час паузи
    current_height = driver.execute_script("return document.body.scrollHeight")
    
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause_time)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == current_height:
            print("[ЛОГ] Додаткових елементів не знайдено. Завантаження завершено.")
            break
        current_height = new_height

# Основний код
base_url = 'https://www.tavriav.ua/ca/%D1%87%D0%B0%D0%B8-%D0%BA%D0%B0%D0%B2%D0%B0-%D1%82%D0%B0-%D0%BA%D0%B0%D0%BA%D0%B0%D0%BE/%D0%BA%D0%B0%D0%B2%D0%BE%D0%B2%D1%96-%D0%BD%D0%B0%D0%BF%D0%BE%D1%96/9829/9830'
options = webdriver.ChromeOptions()
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-webgl')
options.add_argument('--disable-extensions')
options.add_argument('--disable-cache')
options.add_argument('--incognito')

with webdriver.Chrome(options=options) as driver:
    driver.get(base_url)
    quotes = []
    print("[ЛОГ] Початок скролінгу.")
    scroll_down(driver)  # Прокручування сторінки
    print("[ЛОГ] Завершено скролінг. Початок збору даних.")
    quotes = scrape_page(driver, quotes)

    if quotes:
        header = ['Назва товару', 'Ціна товару(грн)', 'Ціна товару з урахуванням знижки(грн)', 'Стара ціна товару(грн)', 'Відсоток знижки(%)']
        quotes.sort(key=lambda x: x[0])
        df = pd.DataFrame(quotes, columns=header)
        output_file = 'tavria_products.xlsx'
        df.to_excel(output_file, index=False, sheet_name='Products')
        print(f"Файл '{output_file}' успішно створено!")
    else:
        print("[ЛОГ] Дані відсутні. Файл не створено.")
