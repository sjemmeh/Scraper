from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Importeer je scraper functies
import ah_scraper
import jumbo_scraper # <-- Nieuwe import

# Define the request body model for type validation
class ScrapeRequest(BaseModel):
    url: HttpUrl
    supermarket: str

app = FastAPI(title="MealFlow Scraper API")

# Voeg de Jumbo scraper toe aan de mapping
SCRAPER_MAPPING = {
    "Albert Heijn": ah_scraper.scrape_price,
    "Jumbo": jumbo_scraper.scrape_price, # <-- Nieuwe toevoeging
}

@app.post("/scrape")
def handle_scrape_request(request: ScrapeRequest):
    """
    Receives a URL and supermarket name, then scrapes for the price.
    """
    scraper_function = SCRAPER_MAPPING.get(request.supermarket)
    
    if not scraper_function:
        raise HTTPException(status_code=400, detail=f"No scraper available for supermarket: {request.supermarket}")

    # Setup options to connect to the existing Chrome instance
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    
    driver = None
    try:
        # Initialize the driver by connecting to the browser
        driver = webdriver.Chrome(options=chrome_options)
        
        # Call the appropriate scraper function
        result = scraper_function(driver, str(request.url))

        if "error" in result:
            # If the scraper function returned an error, send it back with a 422 status
            raise HTTPException(status_code=422, detail=result["error"])
        
        # If successful, return the data
        return result

    except Exception as e:
        # Handle high-level errors like browser connection failure
        raise HTTPException(status_code=500, detail=f"A server error occurred: {str(e)}")