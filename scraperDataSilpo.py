import requests
from bs4 import BeautifulSoup
import pandas as pd

def scrape_page(soup, quotes):
    quote_elements = soup.find_all('div', class_='.product-card__body')
    for quote_element in quote_elements:
        text = quote_element.find('div', class_='product-card__title').text
        author = quote_element.find('div', class_='.ft-whitespace-nowrap.ft-text-22.ft-font-bold').text
        tag_elements = quote_element.find('div', class_='.ft-typo-14-semibold.xl\\:ft-typo-16-semibold').find_all('span')
        tags = [tag.text for tag in tag_elements]
        quotes.append({
            'Назва товару': text,
            'Ціна товару': author,
            'Вага товару': ', '.join(tags)
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

# Обробка наступних сторінок
next_li_element = soup.find('a', class_='.pagination-item.pagination-item--current.ng-star-inserted')
while next_li_element:
    next_page_relative_url = next_li_element.find('a', href=True)['href']
    page = requests.get(base_url + next_page_relative_url, headers=headers)
    soup = BeautifulSoup(page.text, 'html.parser')
    scrape_page(soup, quotes)
    next_li_element = soup.find('a', class_='.pagination-item.pagination-item--current.ng-star-inserted')

# Збереження у файл Excel
df = pd.DataFrame(quotes)
df.to_excel('quotes.xlsx', index=False, sheet_name='Quotes')

print("Файл 'quotes.xlsx' успішно створено!")
