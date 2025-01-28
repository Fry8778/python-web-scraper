import requests
import pandas as pd

# Унікальний набір товарів для перевірки дублікатів
unique_products = set()

def is_duplicate(product_name, price):
    """Перевірка на дублікати товарів."""
    product_key = (product_name, price)
    if product_key in unique_products:
        return True
    unique_products.add(product_key)
    return False

def extract_value(value, unit=""):
    """Перетворює числове значення у відформатований текст з одиницею."""
    try:
        if value is None:
            return ''
        value = float(value)
        if unit:
            return f"{value:.0f} {unit}"
        return f"{value:.2f} грн"
    except (ValueError, TypeError):
        return str(value).strip()

def fetch_product_data_api(page=1, limit=40):
    """Функція для отримання даних через API Varus."""
    url = "https://deadpool.special-sailfish.instaleap.io/api/v3"
    headers = {
        "Accept": "*/*",
        "Accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7,uk;q=0.6",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Content-Type": "application/json"
    }
    payload = [
        {
            "operationName": "GetProductsByCategory",
            "variables": {
                "getProductsByCategoryInput": {
                    "categoryReference": "9830",
                    "categoryId": "null",
                    "clientId": "TAVRIA_UA",
                    "storeReference": "449",
                    "currentPage": page,
                    "pageSize": limit,
                    "filters": {},
                    "googleAnalyticsSessionId": ""
                }
            },
            "query": """fragment CategoryFields on CategoryModel {
  active
  boost
  hasChildren
  categoryNamesPath
  isAvailableInHome
  level
  name
  path
  reference
  slug
  photoUrl
  imageUrl
  shortName
  isFeatured
  isAssociatedToCatalog
  __typename
}

fragment CatalogProductTagModel on CatalogProductTagModel {
  description
  enabled
  textColor
  filter
  tagReference
  backgroundColor
  name
  __typename
}

fragment CatalogProductFormatModel on CatalogProductFormatModel {
  format
  equivalence
  unitEquivalence
  clickMultiplier
  minQty
  maxQty
  __typename
}

fragment Taxes on ProductTaxModel {
  taxId
  taxName
  taxType
  taxValue
  taxSubTotal
  __typename
}

fragment PromotionCondition on PromotionCondition {
  quantity
  price
  priceBeforeTaxes
  taxTotal
  taxes {
    ...Taxes
    __typename
  }
  __typename
}

fragment Promotion on Promotion {
  type
  isActive
  conditions {
    ...PromotionCondition
    __typename
  }
  description
  endDateTime
  startDateTime
  __typename
}

fragment PromotedModel on PromotedModel {
  isPromoted
  onLoadBeacon
  onClickBeacon
  onViewBeacon
  onBasketChangeBeacon
  onWishlistBeacon
  __typename
}

fragment SpecificationModel on SpecificationModel {
  title
  values {
    label
    value
    __typename
  }
  __typename
}

fragment NutritionalDetailsInformation on NutritionalDetailsInformation {
  servingName
  servingSize
  servingUnit
  servingsPerPortion
  nutritionalTable {
    nutrientName
    quantity
    unit
    quantityPerPortion
    dailyValue
    __typename
  }
  bottomInfo
  __typename
}

fragment CatalogProductModel on CatalogProductModel {
  name
  price
  photosUrl
  unit
  subUnit
  subQty
  description
  sku
  ean
  maxQty
  minQty
  clickMultiplier
  nutritionalDetails
  isActive
  slug
  brand
  stock
  securityStock
  boost
  isAvailable
  location
  priceBeforeTaxes
  taxTotal
  promotion {
    ...Promotion
    __typename
  }
  taxes {
    ...Taxes
    __typename
  }
  categories {
    ...CategoryFields
    __typename
  }
  categoriesData {
    ...CategoryFields
    __typename
  }
  formats {
    ...CatalogProductFormatModel
    __typename
  }
  tags {
    ...CatalogProductTagModel
    __typename
  }
  specifications {
    ...SpecificationModel
    __typename
  }
  promoted {
    ...PromotedModel
    __typename
  }
  score
  relatedProducts
  ingredients
  stockWarning
  nutritionalDetailsInformation {
    ...NutritionalDetailsInformation
    __typename
  }
  productVariants
  isVariant
  isDominant
  __typename
}

fragment CategoryWithProductsModel on CategoryWithProductsModel {
  name
  reference
  level
  path
  hasChildren
  active
  boost
  isAvailableInHome
  slug
  photoUrl
  categoryNamesPath
  imageUrl
  shortName
  isFeatured
  products {
    ...CatalogProductModel
    __typename
  }
  __typename
}

fragment PaginationTotalModel on PaginationTotalModel {
  value
  relation
  __typename
}

fragment PaginationModel on PaginationModel {
  page
  pages
  total {
    ...PaginationTotalModel
    __typename
  }
  __typename
}

fragment AggregateBucketModel on AggregateBucketModel {
  min
  max
  key
  docCount
  __typename
}

fragment AggregateModel on AggregateModel {
  name
  docCount
  buckets {
    ...AggregateBucketModel
    __typename
  }
  __typename
}

fragment BannerModel on BannerModel {
  id
  storeId
  title
  desktopImage
  mobileImage
  targetUrl
  targetUrlInfo {
    type
    url
    __typename
  }
  targetCategory
  index
  categoryId
  __typename
}

query GetProductsByCategory($getProductsByCategoryInput: GetProductsByCategoryInput!) {
  getProductsByCategory(getProductsByCategoryInput: $getProductsByCategoryInput) {
    category {
      ...CategoryWithProductsModel
      __typename
    }
    pagination {
      ...PaginationModel
      __typename
    }
    aggregates {
      ...AggregateModel
      __typename
    }
    banners {
      ...BannerModel
      __typename
    }
    promoted {
      ...PromotedModel
      __typename
    }
    __typename
  }
}"""
        }
    ]
    print(f"[ЛОГ] Тіло запиту: {payload}")
    print(f"[ЛОГ] Заголовки запиту: {headers}")
    try:
        response = requests.post(url, headers=headers, json=payload)
        print(f"[ЛОГ] URL запиту: {response.url}")
        response.raise_for_status()
        data = response.json()
        print(f"[ЛОГ] Відповідь API: {data}")

        # Перевіряємо, чи це список або словник
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return data.get('data', [])
        else:
            print("[ЛОГ] Невідомий формат відповіді.")
            return []
    except requests.RequestException as e:
        print(f"[ЛОГ] Помилка запиту до API: {e}")
        return []

def save_to_excel(data, filename='tavriaV_kava_v_zernakh_api.xlsx'):
    """Функція для запису даних у Excel."""
    if not data:
        print("[ЛОГ] Немає даних для запису у файл.")
        return

    header = [
        'Назва товару', 'Ціна (грн)', 'Ціна зі знижкою (грн)', 'Знижка (%)'
    ]
    data.sort(key=lambda x: x[0])
    df = pd.DataFrame(data, columns=header)
    df.to_excel(filename, index=False, sheet_name='Products')
    print(f"Файл '{filename}' успішно створено!")

def fetch_and_save_data_api(filename='tavriaV_kava_v_zernakh_api.xlsx', limit=40):
    """Основна функція для збору даних і збереження у файл."""
    page = 1
    product_list = []

    while True:
        products = fetch_product_data_api(page, limit)
        if not products:
            print("[ЛОГ] Дані не знайдено або помилка при завантаженні.")
            break

        print(f"[ЛОГ] Завантажено продуктів: {len(products)} на сторінці {page}")

        for product in products:
            try:
                product_name = product.get('name', '').strip()
                price = product.get('price', 0)
                # Витягнення ціни зі знижкою
                price_with_discount = product.get('promotion', {}).get('conditions', [{}])[0].get('price', price)
                
                # Обчислення знижки, якщо вона є
                if price > price_with_discount:
                    discount = round(((price - price_with_discount) / price) * 100, 2)
                else:
                    discount = 0

                # Перевірка на наявність товару на складі
                if product.get('stock', 0) <= 0:
                    print(f"[ЛОГ] Пропущено (відсутній на складі): {product_name}, stock: {product.get('stock', 'N/A')}")
                    continue

                # Перевірка на дублікати
                if is_duplicate(product_name, price):
                    print(f"[ЛОГ] Пропущено (дублікат): {product_name}")
                    continue

                # Додавання продукту до списку
                product_list.append([
                    product_name, 
                    extract_value(price), 
                    extract_value(price_with_discount), 
                    f"{discount:.2f}%" if discount > 0 else '', 
                ])
            except Exception as e:
                print(f"[ЛОГ] Помилка обробки продукту: {e}")
        
        if len(products) < limit:
            print("[ЛОГ] Завантажено останню сторінку.")
            break

        page += 1

    print(f"[ЛОГ] Усього продуктів для запису: {len(product_list)}")
    save_to_excel(product_list, filename)

# Виклик функції
fetch_and_save_data_api(limit=40)