from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import os
import time
import json
import csv

# Setup Selenium WebDriver
options = Options()
options.add_argument('--headless')
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
chromedriver_path = os.getenv("CHROMEDRIVER_PATH", "D:\\chromedriver-win64\\chromedriver-win64\\chromedriver.exe")

# Verify the path to chromedriver
if not os.path.exists(chromedriver_path):
    raise FileNotFoundError(f"Chromedriver not found at {chromedriver_path}")

try:
    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=options)
except Exception as e:
    raise RuntimeError(f"Error initializing WebDriver: {e}")

# Amazon login function
def amazon_login(driver, username, password):
    driver.get("https://www.amazon.in/ap/signin")

    # Enter email or phone number
    email_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "ap_email"))
    )
    email_field.send_keys(username)
    driver.find_element(By.ID, "continue").click()

    # Enter password
    password_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "ap_password"))
    )
    password_field.send_keys(password)

    # Click login
    driver.find_element(By.ID, "signInSubmit").click()

# Scrape category function
def scrape_category(driver, category_url, category_name):
    driver.get(category_url)

    products = []
    try:
        for i in range(1, 21):  # Limit to top 1500 products (~75 per page * 20 pages)
            product_cards = driver.find_elements(By.CSS_SELECTOR, ".zg-item-immersion")

            for product in product_cards:
                try:
                    name = product.find_element(By.CSS_SELECTOR, ".p13n-sc-truncated").text
                    price = product.find_element(By.CSS_SELECTOR, ".p13n-sc-price").text
                    discount = product.find_element(By.CSS_SELECTOR, ".a-row.a-size-small span").text if product.find_elements(By.CSS_SELECTOR, ".a-row.a-size-small span") else "N/A"
                    rating = product.find_element(By.CSS_SELECTOR, ".a-icon-alt").text if product.find_elements(By.CSS_SELECTOR, ".a-icon-alt") else "N/A"
                    seller = "N/A"  # Placeholder for Ship From and Sold By info
                    description = product.find_element(By.CSS_SELECTOR, ".a-section.a-spacing-none.p13n-asin-description").text if product.find_elements(By.CSS_SELECTOR, ".a-section.a-spacing-none.p13n-asin-description") else "N/A"
                    images = [img.get_attribute("src") for img in product.find_elements(By.CSS_SELECTOR, "img")]

                    # Append product details
                    products.append({
                        "Product Name": name,
                        "Price": price,
                        "Discount": discount,
                        "Rating": rating,
                        "Ship From": "N/A",
                        "Sold By": seller,
                        "Description": description,
                        "Images": images,
                        "Category": category_name
                    })
                except Exception as e:
                    print(f"Error extracting product details: {e}")

            # Navigate to the next page
            try:
                next_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".a-last a"))
                )
                next_button.click()
                time.sleep(2)  # Wait for page load
            except Exception as e:
                print(f"No more pages or error navigating to next page: {e}")
                break

    except Exception as e:
        print(f"Error navigating category pages: {e}")

    return products

# Main function
def main():
    username = os.getenv("AMAZON_USERNAME", "harshithaksherasagar@gmail.com")  # Replace with your Amazon username
    password = os.getenv("AMAZON_PASSWORD", "Harshitha12345@")  # Replace with your Amazon password

    try:
        amazon_login(driver, username, password)
    except Exception as e:
        print(f"Error during login: {e}")
        driver.quit()
        raise

    categories = [
        {"url": "https://www.amazon.in/gp/bestsellers/kitchen/ref=zg_bs_nav_kitchen_0", "name": "Kitchen"},
        {"url": "https://www.amazon.in/gp/bestsellers/shoes/ref=zg_bs_nav_shoes_0", "name": "Shoes"},
        {"url": "https://www.amazon.in/gp/bestsellers/computers/ref=zg_bs_nav_computers_0", "name": "Computers"},
        {"url": "https://www.amazon.in/gp/bestsellers/electronics/ref=zg_bs_nav_electronics_0", "name": "Electronics"},
        # Add more categories as needed
    ]

    all_products = []

    for category in categories:
        print(f"Scraping category: {category['name']}")
        products = scrape_category(driver, category['url'], category['name'])
        all_products.extend(products)

    # Save data to JSON and CSV
    if all_products:
        with open("products.json", "w") as json_file:
            json.dump(all_products, json_file, indent=4)

        with open("products.csv", "w", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=all_products[0].keys())
            writer.writeheader()
            writer.writerows(all_products)

    driver.quit()

if __name__ == "__main__":
    main()