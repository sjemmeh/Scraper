import undetected_chromedriver as uc
import jumbo_scraper # We testen alleen met de scraper die werkte
import traceback
import sys

# Dit script negeert de API en test de scrape-functie direct.
TEST_URL = "https://www.jumbo.com/producten/unox-good-noodles-cup-kip-65-g-358686CUP"

def run_test():
    print("--- START DIRECTE SCRAPE TEST ---")
    
    options = uc.ChromeOptions()

    # We proberen het ZONDER headless, zodat je een venster zou moeten zien.
    # options.add_argument('--headless=new') 
    
    # Dit zijn de belangrijkste opties om het te laten werken in een server-omgeving
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36')

    driver = None
    try:
        print("Poging om uc.Chrome() te initialiseren...")
        # Dit is het kritieke moment. Hier zou een browserproces moeten starten.
        driver = uc.Chrome(options=options, use_subprocess=True)
        print("SUCCES: Chrome driver is geïnitialiseerd.")
        
        # Roep de jumbo scraper direct aan
        result = jumbo_scraper.scrape_price(driver, TEST_URL)
        
        print("\n--- RESULTAAT ---")
        print(result)
        print("-----------------")

    except Exception as e:
        print("\n!!! ER IS EEN FATALE FOUT OPGETREDEN !!!", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
    finally:
        if driver:
            print("Driver wordt afgesloten.")
            driver.quit()

# Voer de testfunctie uit
if __name__ == "__main__":
    run_test()