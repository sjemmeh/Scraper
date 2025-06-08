import undetected_chromedriver as uc
import sys
import traceback

print("--- START CHROME LAUNCH TEST ---")

try:
    print("1. Opties aanmaken...")
    options = uc.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    print("Opties succesvol aangemaakt.")

    print("2. Proberen om uc.Chrome() te initialiseren...")
    # Dit is de regel waar het waarschijnlijk misgaat
    driver = uc.Chrome(options=options, use_subprocess=True)
    
    print("3. SUCCES! Chrome driver is gestart.")
    
    print("4. Proberen om een pagina te laden...")
    driver.get("https://www.google.com")
    print(f"5. Pagina titel is: {driver.title}")
    
    print("6. Driver wordt afgesloten.")
    driver.quit()
    
    print("--- EINDE TEST (SUCCES) ---")

except Exception as e:
    print("!!! FOUT TIJDENS HET STARTEN VAN CHROME !!!", file=sys.stderr)
    # Print de volledige foutmelding (traceback)
    traceback.print_exc(file=sys.stderr)
