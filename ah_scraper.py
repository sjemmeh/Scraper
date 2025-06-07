import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def scrape_price(driver, url):
    """
    Uses the provided Selenium driver to scrape a product URL from Albert Heijn.
    """
    # XPaths for sale and regular prices
    sale_price_xpath = "//*[@id='start-of-content']/div[1]/div/div/div/div/article/div/div/div[2]/div[2]/div[1]/div[2]/span[1]"
    regular_price_xpath = "//*[@id='start-of-content']/div[1]/div/div/div/div/article/div/div/div[2]/div[2]/div[1]/div/span[1]"

    try:
        driver.get(url)
        # Wait for a key element to ensure page has started rendering
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "start-of-content"))
        )
        
        aria_label = None
        
        # Try to find the sale price first
        try:
            sale_element = driver.find_element(By.XPATH, sale_price_xpath)
            aria_label = sale_element.get_attribute("aria-label")
        except NoSuchElementException:
            try:
                regular_element = driver.find_element(By.XPATH, regular_price_xpath)
                aria_label = regular_element.get_attribute("aria-label")
            except NoSuchElementException:
                return {"error": "Price element not found"}

        if aria_label:
            match = re.search(r'€\s*([0-9,.]+)', aria_label)
            if match:
                price_str = match.group(1).replace('.', '').replace(',', '.')
                price = float(price_str)
                return {"price": price, "currency": "EUR"}
            else:
                return {"error": f"Could not parse price from aria-label: '{aria_label}'"}
        
        return {"error": "Price element found but no aria-label attribute."}

    except TimeoutException:
        return {"error": f"Page timed out while loading: {url}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {str(e)}"}