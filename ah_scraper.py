import re
import time
import random # Importeer de random module voor willekeurige vertragingen
import sys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def scrape_price(driver, url):
    try:
        # --- NIEUWE LOGICA: SIMULEER EEN MENSELIJKE BEZOEKER ---

        # Stap 1: Bezoek eerst de homepage om "echter" over te komen en cookies te accepteren.
        print("Navigeren naar de homepage (ah.nl) om een sessie op te bouwen...", file=sys.stdout)
        driver.get("https://www.ah.nl/")

        # Probeer direct de cookie-banner op de homepage te accepteren
        try:
            cookie_button_xpath = "//button[contains(., 'Alles accepteren')]"
            cookie_button = WebDriverWait(driver, 7).until(
                EC.element_to_be_clickable((By.XPATH, cookie_button_xpath))
            )
            print("Cookie banner gevonden op homepage, proberen te klikken...", file=sys.stdout)
            cookie_button.click()
            # Geef de pagina even de tijd om te herladen na de klik
            time.sleep(random.uniform(1, 3))
        except (TimeoutException, NoSuchElementException, ElementClickInterceptedException):
            print("Geen cookie banner gevonden op homepage, of al geaccepteerd.", file=sys.stdout)
            pass
            
        # Wacht een willekeurige tijd, alsof een mens aan het rondkijken is
        print("Korte pauze om menselijk gedrag te simuleren...", file=sys.stdout)
        time.sleep(random.uniform(2, 5))

        # Stap 2: Navigeer nu pas naar de daadwerkelijke productpagina
        print(f"Navigeren naar de productpagina: {url}", file=sys.stdout)
        driver.get(url)
        
        # --- EINDE NIEUWE NAVIGATIELOGICA ---

        # Wacht nu tot de hoofd-content van de productpagina is geladen
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "start-of-content"))
        )
        
        # De rest van de scrape-logica (prijs zoeken) blijft hetzelfde...
        sale_price_xpath = "//*[@id='start-of-content']/div[1]/div/div/div/div/article/div/div/div[2]/div[2]/div[1]/div[2]/span[1]"
        regular_price_xpath = "//*[@id='start-of-content']/div[1]/div/div/div/div/article/div/div/div[2]/div[2]/div[1]/div/span[1]"
        aria_label = None

        try:
            sale_element = driver.find_element(By.XPATH, sale_price_xpath)
            aria_label = sale_element.get_attribute("aria-label")
        except NoSuchElementException:
            try:
                regular_element = driver.find_element(By.XPATH, regular_price_xpath)
                aria_label = regular_element.get_attribute("aria-label")
            except NoSuchElementException:
                return {"error": "Prijselement niet gevonden voor AH"}

        if aria_label:
            match = re.search(r'€\s*([0-9,.]+)', aria_label)
            if match:
                price_str = match.group(1).replace('.', '').replace(',', '.')
                price = float(price_str)
                return {"price": price, "currency": "EUR"}
            else:
                return {"error": f"Kon prijs niet parsen uit aria-label: '{aria_label}'"}
        
        return {"error": "Prijselement gevonden, maar zonder aria-label"}

    except TimeoutException:
        screenshot_path = f"/home/scrape/mealflow-scraper/logs/timeout_error_ah_{int(time.time())}.png"
        try:
            driver.save_screenshot(screenshot_path)
            print(f"!!! TimeoutException: Screenshot opgeslagen in {screenshot_path}", file=sys.stderr)
            return {"error": f"Pagina laadde niet op tijd. Screenshot is opgeslagen op de server."}
        except Exception as ss_e:
            return {"error": f"Pagina laadde niet op tijd, en screenshot maken mislukte: {ss_e}"}
    except Exception as e:
        return {"error": f"Onverwachte fout opgetreden bij AH scraper: {str(e)}"}