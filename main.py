from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
import undetected_chromedriver as uc  # <-- Gebruik de nieuwe bibliotheek
import ah_scraper
import jumbo_scraper
import sys

class ScrapeRequest(BaseModel):
    url: HttpUrl
    supermarket: str

app = FastAPI(title="MealFlow Stealth Scraper API")

SCRAPER_MAPPING = {
    "Albert Heijn": ah_scraper.scrape_price,
    "Jumbo": jumbo_scraper.scrape_price,
}

@app.post("/scrape")
def handle_scrape_request(request: ScrapeRequest):
    scraper_function = SCRAPER_MAPPING.get(request.supermarket)
    
    if not scraper_function:
        raise HTTPException(status_code=400, detail=f"No scraper available for supermarket: {request.supermarket}")

    print(f"--- STARTING STEALTH SCRAPE: {request.supermarket} - {request.url} ---", file=sys.stdout)

    # Opties voor de undetected_chromedriver
    options = uc.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu') # Soms nodig voor headless in VMs
    options.add_argument('--window-size=1920,1080')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36')
    
    driver = None
    try:
        print("Initializing undetected-chromedriver...", file=sys.stdout)
        # Start de gepatchte, ondetecteerbare Chrome-browser
        driver = uc.Chrome(options=options, use_subprocess=True)
        print("Driver initialized successfully.", file=sys.stdout)
        
        # Roep de scraper-functie aan (deze hoeven niet te veranderen)
        result = scraper_function(driver, str(request.url))
        print(f"Scraper function executed. Result: {result}", file=sys.stdout)

        if "error" in result:
            raise HTTPException(status_code=422, detail=result["error"])
        
        return result

    except Exception as e:
        error_message = f"An unexpected error occurred in main.py: {str(e)}"
        print(f"!!! {error_message}", file=sys.stderr)
        raise HTTPException(status_code=500, detail=error_message)
    finally:
        # Sluit de browser altijd af na de taak
        if driver:
            print("Closing driver.", file=sys.stdout)
            driver.quit()