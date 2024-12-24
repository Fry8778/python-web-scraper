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
        WebDriverWait(driver, 30).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "product-card__body"))
        )
        products = driver.find_elements(By.CLASS_NAME, "product-card__body")

        if not products:
            print("[ЛОГ] Продукти не знайдені на сторінці.")
            return quotes

        # Перевірка чи є нові продукти
        current_product_count = len(products)
        if current_product_count == 0:
            print("[ЛОГ] Немає нових продуктів на сторінці. Завантаження завершено.")
            return quotes

        for index, product in enumerate(products):
            retry_count = 3  # Число спроб
            while retry_count > 0:
                try:
                    product_name_element = WebDriverWait(product, 5).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "product-card__title"))
                    )
                    product_name = product_name_element.text.strip()

                    if is_duplicate(product_name):
                        break

                    weight_element = product.find_element(By.CLASS_NAME, "ft-typo-14-semibold")
                    weight = weight_element.text.strip() if weight_element else ''

                    # Збір цін та знижок, із додаванням обробки кешу та асинхронних завантажень
                    special_price_elements = product.find_elements(By.CSS_SELECTOR, "div.product-card-price div.ft-whitespace-nowrap.ft-text-22.ft-font-bold")
                    sale_price_elements = product.find_elements(By.CSS_SELECTOR, "div.product-card-price__old div.ft-line-through")
                    discount_elements = product.find_elements(By.CSS_SELECTOR, "div.product-card-price__old div.product-card-price__sale")

                    # Перевірка правильності зібраних елементів
                    if not special_price_elements or not sale_price_elements or not discount_elements:
                        price_element = product.find_element(By.CSS_SELECTOR, "div.product-card-price div.ft-whitespace-nowrap.ft-text-22.ft-font-bold")
                        price = price_element.text.strip() if price_element else ''
                        special_price = ''
                        sale_price = ''
                        discount = ''
                    else:
                        price = ''
                        special_price = special_price_elements[0].text.strip() if special_price_elements else ''
                        sale_price = sale_price_elements[0].text.strip() if sale_price_elements else ''
                        discount = discount_elements[0].text.strip() if discount_elements else ''

                    # Додавання логування і перевірки кешу
                    print(f"[ЛОГ] Старі дані для {product_name}: ціна = {special_price}, знижка = {discount}")

                    # Перевірка правильності відсотка знижки (можна додати перерахунок якщо потрібно)
                    if sale_price and special_price:
                        try:
                            old_price = float(special_price.replace(" грн", "").replace(",", "."))
                            new_price = float(sale_price.replace(" грн", "").replace(",", "."))
                            calculated_discount = round((old_price - new_price) / old_price * 100)
                            if discount:
                                print(f"[ЛОГ] Перерахований відсоток знижки: {calculated_discount}% (на сайті {discount})")
                        except ValueError:
                            print(f"[ЛОГ] Помилка при перерахунку знижки для {product_name}")

                    quotes.append([product_name,
                                   price,
                                   weight,
                                   special_price,
                                   sale_price,
                                   discount
                    ])
                    print(f"[ЛОГ] Додано: {product_name}, Ціна: {price}")
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


# Функція для переходу на наступну сторінку
def go_to_next_page(driver):
    try:
        # Перевірка на наявність кнопки "Наступна сторінка"
        next_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.pagination-item.pagination-item--next-page"))
        )
        # Перевірка чи є наступна сторінка
        if "disabled" in next_button.get_attribute("class"):
            print("[ЛОГ] Це остання сторінка. Завантаження завершено.")
            return False  # Завершити, якщо кнопка відключена (останнє посилання)
        
        driver.execute_script("arguments[0].click();", next_button)
        print("[ЛОГ] Перехід на наступну сторінку.")
        return True
    except TimeoutException:
        print("[ЛОГ] Кнопка наступної сторінки не знайдена або час очікування вичерпано.")
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
options.add_argument('--disable-cache')
options.add_argument('--incognito')


with webdriver.Chrome(options=options) as driver:
    driver.get(base_url)
    quotes = []
    page_number = 1

    while True:
        print(f"[ЛОГ] Завантаження сторінки {page_number}.")
        quotes = scrape_page(driver, quotes)
        time.sleep(random.uniform(3, 7))

        if quotes:
            header = ['Назва товару', 'Ціна товару', 'Вага товару', 'Ціна зі знижкою', 'Стара ціна', 'Відсоток знижки(%)']
            quotes.sort(key=lambda x: x[0])
            df = pd.DataFrame(quotes, columns=header)
            output_file = 'silpo_products.xlsx'
            df.to_excel(output_file, index=False, sheet_name='Products')
            print(f"Файл '{output_file}' успішно оновлено після сторінки {page_number}.")

        if not go_to_next_page(driver):
            print("[ЛОГ] Завантаження завершено.")
            break
        page_number += 1

print(f"Файл '{output_file}' успішно створено!")
