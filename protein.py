import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()

def silent_del(self):
    try:
        if hasattr(self, 'quit'):
            self.quit()
    except:
        pass

uc.Chrome.__del__ = silent_del

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

options = uc.ChromeOptions()
#options.add_argument("--headless")
driver = uc.Chrome(options=options)

BASE_URL = "https://www.hollandandbarrett.com/search/?query=protein%20powder&page={}"

def safe_get_text(by, selector, parent=None):
    try:
        element = (parent or driver).find_element(by, selector)
        return element.text
    except NoSuchElementException:
        return ""

def get_rating_from_width(style_string):
    try:
        if "width:" in style_string:
            percent = float(style_string.strip().split("width:")[1].replace("%", "").replace(";", ""))
            return round(percent / 20, 1)
    except:
        return None

for page in range(1, 41): 
    driver.get(BASE_URL.format(page))
    time.sleep(3)  

    product_cards = driver.find_elements(By.CSS_SELECTOR, "a[data-test^='product-card']")

    for idx, card in enumerate(product_cards):
        data = {}
        data['brand_name'] = safe_get_text(By.CSS_SELECTOR, "div.ProductCard-module_brandName__696T7", card)
        data['title'] = safe_get_text(By.CSS_SELECTOR, "div.ProductCard-module_title__lkpQp", card)
        review_text = safe_get_text(By.CSS_SELECTOR, "div.RatingStars-module_reviewCount__lj-wG", card)
        data['review'] = review_text.strip("()")

        try:
            rating_wrapper = card.find_element(By.CSS_SELECTOR, "div[data-test='rating-stars']")
            star_span = rating_wrapper.find_elements(By.TAG_NAME, "span")[1]
            style = star_span.get_attribute("style")
            data['rating'] = get_rating_from_width(style)
        except:
            data['rating'] = None

        data['discount'] = safe_get_text(By.CSS_SELECTOR, "div.ProductCard-module_promotion__8iZxf", card)
        data['actual_price'] = safe_get_text(By.CSS_SELECTOR, "div.ProductCard-module_salePrice__DVj2z", card)
        data['selling_price'] = safe_get_text(By.CSS_SELECTOR, "div.ProductCard-module_price__OuhCW", card)
        data['amount'] = safe_get_text(By.CLASS_NAME, "ProductCard-module_pricePerUnit__e3Et-", card)


        try:
            existing = supabase.table("protein_datas").select("id").eq("title", data['title']).execute()
            if existing.data:
                supabase.table("protein_datas").update(data).eq("title", data['title']).execute()
            else:
                supabase.table("protein_datas").insert(data).execute()
        except Exception as e:
            print(f"Database error for product {data['title']}: {e}")

driver.quit()

