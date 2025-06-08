from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import ah_scraper
import jumbo_scraper
import sys

class ScrapeRequest(BaseModel):
    url: HttpUrl
    supermarket: str

app = FastAPI(title="MealFlow Headless Scraper API")

SCRAPER_MAPPING = {
    "Albert Heijn": ah_scraper.scrape_price,
    "Jumbo": jumbo_scraper.scrape_price,
}

@app.post("/scrape")
def handle_scrape_request(request: ScrapeRequest):
    scraper_function = SCRAPER_MAPPING.get(request.supermarket)
    
    if not scraper_function:
        raise HTTPException(status_code=400, detail=f"No scraper available for supermarket: {request.supermarket}")

    print(f"--- START SCRAPE REQUEST: {request.supermarket} - {request.url} ---", file=sys.stdout)

    chrome_options = Options()

    # --- DEBUG SECTIE: TEST DEZE OPTIES EEN VOOR EEN ---
    #
    # Test 1: Zorg dat alle drie de regels hieronder een # ervoor hebben.
    #         Herstart de service en test. Werkt het nu (ook al wordt AH geblokkeerd)?
    #
    # Test 2: Verwijder de # voor de EERSTE TWEE regels. Sla op, herstart de service en test opnieuw.
    #         Werkt het nog steeds? Dan ligt het aan de derde regel.
    #
    # Test 3: Als Test 2 mislukte, zet dan de # terug voor de eerste twee regels,
    #         en verwijder alleen de # voor de DERDE regel. Herstart en test.
    
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    # -----------------------------------------------------------------

    # Essentiële headless en server-vriendelijke opties
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")
    
    driver = None
    try:
        print("Stap 1: Initialiseren van de Chrome driver...", file=sys.stdout)
        driver = webdriver.Chrome(options=chrome_options)
        print("Stap 2: Chrome driver succesvol geïnitialiseerd.", file=sys.stdout)
        
        result = scraper_function(driver, str(request.url))
        print(f"Stap 3: Scraper functie uitgevoerd. Resultaat: {result}", file=sys.stdout)

        if "error" in result:
            print(f"Fout geretourneerd door scraper module: {result['error']}", file=sys.stderr)
            raise HTTPException(status_code=422, detail=result["error"])
        
        print("--- EINDE SCRAPE REQUEST (SUCCESS) ---", file=sys.stdout)
        return result

    except Exception as e:
        print(f"!!! ONVERWACHTE FOUT in handle_scrape_request: {str(e)}", file=sys.stderr)
        raise HTTPException(status_code=500, detail=f"A server error occurred: {str(e)}")
    finally:
        if driver:
            print("Stap 4: Chrome driver wordt afgesloten.", file=sys.stdout)
            driver.quit()