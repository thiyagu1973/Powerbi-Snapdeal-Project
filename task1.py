import time
import re
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException

# ================= CONFIG =================
OUTPUT_FILE = "snapdeal.task1.csv"
TARGET_PER_SECTION = 60  # Smaller chunks to prevent browser crashes
SECTIONS = {
    "Accessories": "https://www.snapdeal.com/search?keyword=accessories",
    "Footwear": "https://www.snapdeal.com/search?keyword=footwear",
    "Kids Fashion": "https://www.snapdeal.com/search?keyword=kids%20fashion",
    "Men Clothing": "https://www.snapdeal.com/search?keyword=men%20clothing",
    "Women Clothing": "https://www.snapdeal.com/search?keyword=women%20clothing"
}

options = Options()
# Prevents the "disconnected" error by keeping the session stable
options.add_experimental_option("detach", True)
options.add_argument("--disable-blink-features=AutomationControlled")
driver = webdriver.Chrome(options=options)

all_data = []

print(f"--- 🚀 STATUS: WEBSITE SCRAPPING STARTING FOR TASK 2 ---")

try:
    for section, url in SECTIONS.items():
        print(f"📂 Scraping Section: {section}")
        driver.get(url)
        time.sleep(4)  # Increased wait for stability

        # Robust Scroll Logic
        last_height = driver.execute_script("return document.body.scrollHeight")
        while len(driver.find_elements(By.CSS_SELECTOR, "div.product-tuple-listing")) < TARGET_PER_SECTION:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height: break
            last_height = new_height
            print(f"   > Items loaded: {len(driver.find_elements(By.CSS_SELECTOR, 'div.product-tuple-listing'))}")

        products = driver.find_elements(By.CSS_SELECTOR, "div.product-tuple-listing")
        for item in products[:TARGET_PER_SECTION]:
            try:
                name = item.find_element(By.CSS_SELECTOR, "p.product-title").text

                # Handling Discount Extraction
                try:
                    disc_text = item.find_element(By.CSS_SELECTOR, "span.product-discount").text
                    discount = int(re.search(r'\d+', disc_text).group())
                except:
                    discount = 0

                # Handling Rating Extraction
                rating = float(item.get_attribute("data-rating") or 0)

                all_data.append({
                    "Scraped At": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Section": section,
                    "Product Name": name,
                    "Discount": discount,
                    "Rating": rating
                })
            except Exception as e:
                continue

except WebDriverException as e:
    print(f"❌ Browser Connection Error: {e}")
finally:
    # Save whatever data we got before the crash
    if all_data:
        df = pd.DataFrame(all_data)
        df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
        print(f"--- ✅ SUCCESS: {len(df)} PRODUCTS SAVED TO {OUTPUT_FILE} ---")
    driver.quit()
