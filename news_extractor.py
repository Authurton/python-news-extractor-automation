import os
import time
import pandas as pd
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
from selenium.common.exceptions import TimeoutException
from tqdm import tqdm
from selenium.webdriver.support.ui import Select

class NewsExtractor:
    def __init__(self, search_phrase, news_category, months_to_extract):
        self.search_phrase = search_phrase
        self.news_category = news_category
        self.months_to_extract = months_to_extract
        self.driver = webdriver.Chrome()
    
    def extract_news(self):
        self.driver.get("https://www.latimes.com/")

        # Find search icon using explicit wait with presence_of_element_located
        search_icon_locator = (By.CSS_SELECTOR, "svg[data-element='magnify-icon']")
        search_icon = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located(search_icon_locator)
        )
        search_icon.click()

        # Find search field using explicit wait
        search_field_locator = (By.TAG_NAME, "input")
        search_field = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located(search_field_locator)
        )

        # Enter search phrase and submit
        search_field.send_keys(self.search_phrase)
        search_field.submit()

        time.sleep(5)
        sort_dropdown = Select(self.driver.find_element(By.CLASS_NAME, "select-input"))
        sort_dropdown.select_by_value("1") 

        # need to do topics

        time.sleep(10) 
        news_articles = []
        start_date = datetime.now() - timedelta(days=self.months_to_extract * 30)
        end_date = datetime.now()

        # Find all article elements within a reasonable timeout
        article_elements = WebDriverWait(self.driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "h3.promo-title a.link"))
        )

        article_urls = []
        for article in tqdm(article_elements, desc="Extracting article URLs", unit="element"):
            try:
                article_url = article.get_attribute("href")
                article_urls.append(article_url)
            except Exception as e:
                print(f"Error getting URL for article element: {e}")

        for article_url in tqdm(article_urls, desc="Extracting articles", unit="article"):
            extracted_data = self.process_article(article_url, start_date, end_date)
            if extracted_data:  
                news_articles.append(extracted_data)

        self.driver.quit()
        return news_articles

    def process_article(self, article_url, start_date, end_date):
        try:
            self.driver.get(article_url)

            # Find elements using more generic selectors (adjust if needed)
            title_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h1.headline"))
            )
            description_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "p"))
            )
            image_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "img.image"))
            )

            date_text_element = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "time"))
            )
            date_text = date_text_element.get_attribute("datetime")
            date = datetime.strptime(date_text, "%Y-%m-%dT%H:%M:%S.%fZ")

            if date >= start_date and date <= end_date:
                title = title_element.text
                description = description_element.text
                image_src = image_element.get_attribute("src")
                image_filename = self.download_image(image_src)
                search_phrase_count = self.count_search_phrase(title, description)
                has_money = self.contains_money(title, description)
                print(f"{title}: title, {description}: description, {image_filename}:image file, {search_phrase_count}: count, {has_money}: money")

                return { 
                    "title": title,
                    "date": date,
                    "description": description,
                    "image_filename": image_filename,
                    "search_phrase_count": search_phrase_count,
                    "has_money": has_money
                }
            else:
                return None  

        except Exception as e:
            print(f"Error extracting article details from {article_url}: {e}")
            return None  

    def download_image(self, image_url):
        filename = f"{os.path.splitext(os.path.basename(image_url))[0]}.jpg"
        self.driver.execute_script(f"window.open('{image_url}', '_blank');")
        self.driver.switch_to.window(self.driver.window_handles[1])
        self.driver.save_screenshot(filename)
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])
        return filename

    def count_search_phrase(self, title, description):
        return (title.lower().count(self.search_phrase.lower()) +
                description.lower().count(self.search_phrase.lower()))

    def contains_money(self, title, description):
        money_pattern = r"\$\d+(?:[,\.\d]+)?\b|\b\d+(?:[,\.\d]+)?\s(?:dollars|USD)\b"
        return bool(re.search(money_pattern, title.lower() + " " + description.lower()))

if __name__ == "__main__":
    search_phrase = "climate change"
    news_category = "climate"
    months_to_extract = 3

    extractor = NewsExtractor(search_phrase, news_category, months_to_extract)
    news_articles = extractor.extract_news()

    if not news_articles:  
        print("No articles found for the specified search term or timeframe.")
    else:
        df = pd.DataFrame(news_articles)
        df.to_excel('news_articles.xlsx', index=False, engine='xlsxwriter')