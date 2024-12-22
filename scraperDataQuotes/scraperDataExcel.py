import requests
from bs4 import BeautifulSoup
import pandas as pd

def scrape_page(soup, quotes):
    quote_elements = soup.find_all('div', class_='quote')
    for quote_element in quote_elements:
        text = quote_element.find('span', class_='text').text
        author = quote_element.find('small', class_='author').text
        tag_elements = quote_element.find('div', class_='tags').find_all('a', class_='tag')
        tags = [tag.text for tag in tag_elements]
        quotes.append({
            'Text': text,
            'Author': author,
            'Tags': ', '.join(tags)
        })

# URL сайту
base_url = 'https://quotes.toscrape.com'

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
next_li_element = soup.find('li', class_='next')
while next_li_element:
    next_page_relative_url = next_li_element.find('a', href=True)['href']
    page = requests.get(base_url + next_page_relative_url, headers=headers)
    soup = BeautifulSoup(page.text, 'html.parser')
    scrape_page(soup, quotes)
    next_li_element = soup.find('li', class_='next')

# Збереження у файл Excel
df = pd.DataFrame(quotes)
df.to_excel('quotes.xlsx', index=False, sheet_name='Quotes')

print("Файл 'quotes.xlsx' успішно створено!")
