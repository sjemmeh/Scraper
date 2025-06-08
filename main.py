from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Importeer je scraper functies
import ah_scraper
import jumbo_scraper

# Definieert het formaat van de binnenkomende requests
class ScrapeRequest(BaseModel):
    url: HttpUrl
    supermarket: str

app = FastAPI(title="MealFlow Headless Scraper API")

# Koppelt een supermarktnaam aan de juiste scraper-functie
SCRAPER_MAPPING = {
    "Albert Heijn": ah_scraper.scrape_price,
    "Jumbo": jumbo_scraper.scrape_price,
}

@app.post("/scrape")
def handle_scrape_request(request: ScrapeRequest):
    """
    Ontvangt een URL en supermarktnaam, start een headless browser,
    en schraapt de prijs.
    """
    scraper_function = SCRAPER_MAPPING.get(request.supermarket)
    
    if not scraper_function:
        raise HTTPException(status_code=400, detail=f"No scraper available for supermarket: {request.supermarket}")

    # Setup van de opties voor een headless Chrome instance
    chrome_options = Options()

    # --- Opties om detectie te omzeilen ---
    # 1. Verberg de "Chrome wordt bestuurd door..." infobalk.
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # 2. Verander de 'navigator.webdriver' property van true naar false.
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    # --- Standaard headless en server-vriendelijke opties ---
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")
    
    driver = None
    try:
        # Initialiseer een nieuwe driver met de headless opties
        driver = webdriver.Chrome(options=chrome_options)
        
        # Roep de juiste scraper-functie aan met de nieuwe driver
        result = scraper_function(driver, str(request.url))

        if "error" in result:
            raise HTTPException(status_code=422, detail=result["error"])
        
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"A server error occurred: {str(e)}")
    finally:
        # Belangrijk: sluit de browser na elke scrape-taak om geheugen vrij te maken
        if driver:
            driver.quit()