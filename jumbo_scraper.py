# mealflow-scraper/jumbo_scraper.py
import re
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def scrape_price(driver, url):
    """
    Gebruikt de actieve Selenium driver om een productpagina van Jumbo te scrapen,
    met een extra controle op de tekstinhoud van het prijselement.
    """
    # De nieuwe, door jou opgegeven XPaths
    sale_price_xpath = '//*[@id="mainContent"]/div[2]/div/div[2]/div[1]/div[2]/div[2]/div[2]/div'
    regular_price_xpath = '//*[@id="mainContent"]/div[2]/div/div[2]/div[1]/div[2]/div[2]/div[1]/div'

    try:
        driver.get(url)
        # Wacht tot de hoofdpagina-container geladen is
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "mainContent"))
        )
        
        price_text = None
        
        # Probeer eerst de aanbiedingsprijs te vinden
        try:
            sale_element = driver.find_element(By.XPATH, sale_price_xpath)
            # Controleer direct of de tekst de juiste sleutelwoorden bevat
            if "Nieuwe prijs:" in sale_element.text:
                price_text = sale_element.text
        except NoSuchElementException:
            # Deze exceptie is nu normaal als er geen aanbieding is, dus we gaan gewoon door
            pass

        # Als er geen aanbiedingsprijs is gevonden, zoek dan de normale prijs
        if not price_text:
            try:
                regular_element = driver.find_element(By.XPATH, regular_price_xpath)
                # Controleer ook hier op de juiste sleutelwoorden
                if "Prijs:" in regular_element.text:
                    price_text = regular_element.text
            except NoSuchElementException:
                 # Als ook de normale prijs niet wordt gevonden, loggen we een fout
                return {"error": "Geen geldig prijs-element gevonden (normaal of aanbieding)"}

        # Als we een geldige price_text hebben, parse deze dan
        if price_text:
            # Regex zoekt naar het euroteken gevolgd door het getal
            match = re.search(r'€\s*([0-9,.]+)', price_text)
            if match:
                # Converteer prijs naar een correct float-getal (komma -> punt)
                price_str = match.group(1).replace('.', '').replace(',', '.')
                price = float(price_str)
                return {"price": price, "currency": "EUR"}
            else:
                return {"error": f"Kon prijs niet parsen uit gevonden tekst: '{price_text}'"}
        
        # Dit punt wordt bereikt als er wel een element is gevonden, maar de tekst niet de sleutelwoorden bevatte
        return {"error": "Prijs-element gevonden, maar de tekst bevatte niet 'Prijs:' of 'Nieuwe prijs:'"}

    except TimeoutException:
        return {"error": f"Pagina laadde niet op tijd (timeout): {url}"}
    except Exception as e:
        return {"error": f"Onverwachte fout opgetreden: {str(e)}"}