import time
import random
import json
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# Constants
AMAZON_LOGIN_URL = "https://amc.amazon.com/ap/signin?clientContext=133-8294563-2404362&openid.return_to=https%3A%2F%2Famc.amazon.com%2F&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.assoc_handle=amzn_amcentral_us&openid.mode=checkid_setup&language=en_US&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0"
BEST_SELLERS_URL = "https://www.amazon.com/Best-Sellers/zgbs"
CATEGORIES = 10  
MAX_PRODUCTS = 1500  
# Credentials (replace with your Amazon credentials)
USERNAME = "" 
PASSWORD = ""

# Initialize the WebDriver
def init_driver(headless=False):
    options = Options()
    if headless:
        options.add_argument("--headless")  # Run browser in headless mode
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920x1080")
    
    # Disable automation flags
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    # Specify the path to the ChromeDriver executable
    service = Service("D:\\chromedriver-win64\\chromedriver-win64\\chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=options)
    return driver

# Randomized sleep to simulate human behavior
def human_like_delay():
    time.sleep(random.uniform(1.5, 3.5))  # Random delay between actions

# Login to Amazon
def login_amazon(driver):
    print("Attempting to log in...")
    driver.get(AMAZON_LOGIN_URL)
    
    try:
        # Enter email
        email_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "ap_email"))
        )
        email_field.send_keys(USERNAME)
        driver.find_element(By.ID, "continue").click()
        human_like_delay()

        # Enter password
        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "ap_password"))
        )
        password_field.send_keys(PASSWORD)
        password_field.send_keys(Keys.RETURN)
        human_like_delay()

        # Check for CAPTCHA
        captcha_element = driver.find_elements(By.ID, "auth-captcha-image")
        if captcha_element:
            solve_captcha(driver)  # Placeholder for CAPTCHA solving function

        # Wait a bit longer after CAPTCHA solution
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "nav-link-accountList"))
        )

        print("Login successful.")
    except TimeoutException:
        print("Login failed. Check your credentials or solve CAPTCHA.")
        driver.quit()
        exit()

# Scrape a single category
def scrape_category(driver, category_url):
    print(f"Scraping category: {category_url}")
    driver.get(category_url)
    products = []
    try:
        while len(products) < MAX_PRODUCTS:
            product_elements = driver.find_elements(By.CLASS_NAME, "zg-item-immersion")
            for product in product_elements:
                try:
                    product_name = product.find_element(By.CLASS_NAME, "p13n-sc-truncate").text
                    price = product.find_element(By.CLASS_NAME, "p13n-sc-price").text
                    discount = "N/A"  # Placeholder for discount logic
                    
                    # Try extracting discount if available
                    try:
                        discount_element = product.find_element(By.CLASS_NAME, "p13n-sc-price")
                        discount = discount_element.text
                    except NoSuchElementException:
                        discount = "N/A"

                    rating = product.find_element(By.CLASS_NAME, "a-icon-alt").text
                    category_name = driver.find_element(By.CLASS_NAME, "zg_selected").text

                    # Scrape all images
                    images = [
                        img.get_attribute("src")
                        for img in product.find_elements(By.TAG_NAME, "img")
                    ]

                    products.append({
                        "Product Name": product_name,
                        "Product Price": price,
                        "Sale Discount": discount,
                        "Rating": rating,
                        "Category Name": category_name,
                        "All Available Images": images
                    })

                    if len(products) >= MAX_PRODUCTS:
                        break

                except NoSuchElementException:
                    continue

            # Pagination improvement: Check if the "Next" button is clickable
            try:
                next_button = driver.find_element(By.CLASS_NAME, "a-last")
                if "a-disabled" in next_button.get_attribute("class"):
                    break
                # Use a wait to ensure the button is clickable
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable(next_button))
                next_button.click()
                human_like_delay()  # Add random delay between actions
            except (NoSuchElementException, StaleElementReferenceException):
                break

    except Exception as e:
        print(f"Error scraping category: {e}")

    return products

# Save data to a file
def save_data(data, filename, format="csv"):
    print(f"Saving data to {filename} in {format} format...")
    if format == "csv":
        keys = data[0].keys()
        with open(filename, "w", newline="", encoding="utf-8") as output_file:
            dict_writer = csv.DictWriter(output_file, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(data)
    elif format == "json":
        with open(filename, "w", encoding="utf-8") as output_file:
            json.dump(data, output_file, indent=4, ensure_ascii=False)

# Main function
def main():
    driver = init_driver(headless=False)  # Set headless=False for debugging
    try:
        login_amazon(driver)
        driver.get(BEST_SELLERS_URL)

        # Extract category URLs
        category_elements = driver.find_elements(By.CLASS_NAME, "zg_homeWidget")[:CATEGORIES]
        category_urls = [cat.find_element(By.TAG_NAME, "a").get_attribute("href") for cat in category_elements]

        all_products = []
        for url in category_urls:
            products = scrape_category(driver, url)
            all_products.extend(products)

        # Save to file
        save_data(all_products, "amazon_best_sellers.csv", format="csv")
        print("Data scraping completed successfully.")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
