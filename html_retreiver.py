import time
import re
from datetime import datetime
from urllib.parse import urlparse
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ===================== CONFIG =====================
OUTPUT_CSV = "snapdeal_products.csv"
HEADLESS = False
SCROLL_PAUSE = 0.8
LISTING_WAIT = 10
PRODUCT_WAIT = 10
MAX_PAGES_PER_SUBCAT = 1
DEEP_SCRAPE = False
LEFT_X_THRESHOLD = 420
MAX_PRODUCTS_PER_SUBCAT = 10

BASE_SECTIONS = {
    "Accessories": "https://www.snapdeal.com/search?keyword=accessories&sort=rlvncy",
    "Footwear": "https://www.snapdeal.com/search?keyword=footwear&sort=rlvncy",
    "Kids Fashion": "https://www.snapdeal.com/search?keyword=kids%20fashion&sort=rlvncy",
    "Men Clothing": "https://www.snapdeal.com/search?keyword=men%20clothing&sort=rlvncy",
    "Women Clothing": "https://www.snapdeal.com/search?keyword=women%20clothing&sort=rlvncy",
}
# ==================================================

# ---------- Selenium setup ----------
chrome_opts = Options()
if HEADLESS:
    chrome_opts.add_argument("--headless=new")

chrome_opts.add_argument("--disable-gpu")
chrome_opts.add_argument("--window-size=1920,1080")
chrome_opts.add_argument("--no-sandbox")
chrome_opts.add_argument("--disable-dev-shm-usage")
chrome_opts.add_argument("--remote-allow-origins=*")

# ✅ IMPORTANT FIX: no ChromeDriverManager
driver = webdriver.Chrome(options=chrome_opts)
wait = WebDriverWait(driver, LISTING_WAIT)

# ---------- Helper functions ----------
def human_sleep(sec):
    time.sleep(sec)

def clean_int(text):
    if not text:
        return 0
    nums = re.findall(r"\d+", text)
    return int(nums[0]) if nums else 0

def parse_rating_from_style(style):
    if not style:
        return ""
    m = re.search(r"(\d+(?:\.\d+)?)\s*%", style)
    if not m:
        return ""
    pct = float(m.group(1))
    return round(pct / 20, 1)

def safe_text(el):
    try:
        return el.text.strip()
    except:
        return ""

def find_first(selectors, in_el=None, attr=None):
    ctx = in_el if in_el else driver
    for sel in selectors:
        try:
            el = ctx.find_element(By.CSS_SELECTOR, sel)
            return el.get_attribute(attr) if attr else el.text.strip()
        except:
            continue
    return ""

def find_all(selector, in_el=None):
    ctx = in_el if in_el else driver
    try:
        return ctx.find_elements(By.CSS_SELECTOR, selector)
    except:
        return []

# ---------- Subcategory detection ----------
def get_left_subcategory_links():
    subcats = []
    seen = set()
    for a in driver.find_elements(By.XPATH, "//a[@href]"):
        try:
            href = a.get_attribute("href")
            text = a.text.strip()
            if not text or "snapdeal" not in href:
                continue
            if a.location["x"] < LEFT_X_THRESHOLD:
                key = (text, href)
                if key not in seen:
                    seen.add(key)
                    subcats.append({"Subcategory": text, "URL": href})
        except:
            continue
    return subcats

# ---------- Scrape listing ----------
def scrape_listing_cards(section, subcat, page):
    rows = []
    cards = find_all("div.product-tuple-listing")

    for card in cards[:MAX_PRODUCTS_PER_SUBCAT]:
        name = find_first(["p.product-title"], card)
        price = find_first(["span.product-price"], card)
        rating = find_first([".filled-stars"], card, "style")
        rating = parse_rating_from_style(rating)
        img = find_first(["img"], card, "src")
        url = find_first(["a"], card, "href")

        rows.append({
            "Scraped At": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Section": section,
            "Subcategory": subcat,
            "Product Name": name,
            "Price": price,
            "Rating": rating,
            "Image URL": img,
            "Product URL": url,
            "Page": page
        })
    return rows

# ===================== MAIN =====================
all_rows = []

for section, base_url in BASE_SECTIONS.items():
    print(f"\n=== {section} ===")
    driver.get(base_url)
    human_sleep(3)

    subcats = get_left_subcategory_links()
    if not subcats:
        subcats = [{"Subcategory": "All", "URL": base_url}]

    for sc in subcats:
        print(f"Scraping → {sc['Subcategory']}")
        driver.get(sc["URL"])
        human_sleep(3)

        for page in range(1, MAX_PAGES_PER_SUBCAT + 1):
            rows = scrape_listing_cards(section, sc["Subcategory"], page)
            all_rows.extend(rows)

# ---------- Save CSV ----------
df = pd.DataFrame(all_rows)
df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

print(f"\n✅ DONE! File saved as: {OUTPUT_CSV}")
driver.quit()
