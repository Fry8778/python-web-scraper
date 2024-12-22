import requests
from bs4 import BeautifulSoup
import pandas as pd

def scrape_page(soup, quotes):
    # Пошук всіх товарів
    product_elements = soup.find_all('div', class_='product-card')
    
    for product in product_elements:
        # Назва товару
        title = product.find('div', class_='product-card__title').text.strip()

        # Ціна товару
        price_element = product.find('div', class_='ft-whitespace-nowrap.ft-text-22.ft-font-bold')
        price = price_element.text.strip() if price_element else "Ціна відсутня"

        # Вага товару
        weight_element = product.find('div', class_='ft-typo-14-semibold')
        weight = weight_element.text.strip() if weight_element else "Вага відсутня"

        quotes.append({
            'Назва товару': title,
            'Ціна товару': price,
            'Вага товару': weight
        })

# URL сайту
base_url = 'https://silpo.ua/category/kava-v-zernakh-5111'

# Заголовки для запиту
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'
}

# Запит першої сторінки
page = requests.get(base_url, headers=headers)
soup = BeautifulSoup(page.text, 'html.parser')

# Збір цитат
quotes = []
scrape_page(soup, quotes)

# Збереження у файл Excel
df = pd.DataFrame(quotes)
df.to_excel('silpo_products.xlsx', index=False, sheet_name='Products')

print("Файл 'silpo_products.xlsx' успішно створено!")
