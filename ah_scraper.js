const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());

const sleep = (ms) => new Promise(res => setTimeout(res, ms));
const randomDelay = (min, max) => Math.random() * (max - min) + min;

const scrapeAh = async (url) => {
  let browser = null;
  console.log('Starting AH scrape with Puppeteer-Stealth...');
  try {
    browser = await puppeteer.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--window-size=1920,1080']
    });

    const page = await browser.newPage();
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36');

    // "Menselijke" navigatie blijft hetzelfde
    console.log('Navigating to homepage...');
    await page.goto('https://www.ah.nl/', { waitUntil: 'networkidle2' });
    // ... etc ...

    console.log(`Navigating to product page: ${url}`);
    await page.goto(url, { waitUntil: 'networkidle2' });

    // --- PRIJS ZOEKEN MET DE NIEUWE METHODE ---
    const salePriceXPath = `xpath/${"//*[@id='start-of-content']/div[1]/div/div/div/div/article/div/div/div[2]/div[2]/div[1]/div[2]/span[1]"}`;
    const regularPriceXPath = `xpath/${"//*[@id='start-of-content']/div[1]/div/div/div/div/article/div/div/div[2]/div[2]/div[1]/div/span[1]"}`;
    let ariaLabel = null;
    let element = null;

    try {
      // Wacht maximaal 5 seconden op het sale-element
      element = await page.waitForSelector(salePriceXPath, { timeout: 5000 });
    } catch (e) {
      console.log('Sale price element not found, trying regular price...');
      try {
        // Wacht maximaal 5 seconden op het reguliere element
        element = await page.waitForSelector(regularPriceXPath, { timeout: 5000 });
      } catch (e) {
        console.log('Regular price element also not found.');
      }
    }
    
    if (element) {
        ariaLabel = await page.evaluate(el => el.getAttribute('aria-label'), element);
    }
    
    // --- EINDE NIEUWE METHODE ---

    if (ariaLabel) {
      const match = ariaLabel.match(/€\s*([0-9,.]+)/);
      if (match && match[1]) {
        let priceStr = match[1].replace(/\./g, '').replace(/,/g, '.');
        return { price: parseFloat(priceStr), currency: 'EUR' };
      } else {
        return { error: `Could not parse price from aria-label: '${ariaLabel}'` };
      }
    } else {
      const screenshotPath = `/home/scrape/mealflow-scraper/logs/ah_error_screenshot_${Date.now()}.png`;
      await page.screenshot({ path: screenshotPath });
      return { error: `Price element not found for AH. Screenshot taken at ${screenshotPath}.` };
    }

  } catch (e) {
    console.error('An unexpected error occurred in scrapeAh:', e);
    return { error: e.message };
  } finally {
    if (browser) {
      await browser.close();
      console.log('Browser closed.');
    }
  }
};
 
module.exports = { scrapeAh }; 