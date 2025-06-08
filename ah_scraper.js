// mealflow-scraper/ah_scraper.js
const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());

// Functie voor een willekeurige vertraging
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

    // --- MENSELIJKE NAVIGATIE ---
    console.log('Navigating to homepage...');
    await page.goto('https://www.ah.nl/', { waitUntil: 'networkidle2' });

    try {
      const cookieButtonXPath = "//button[contains(., 'Alles accepteren')]";
      const [cookieButton] = await page.$x(cookieButtonXPath);
      if (cookieButton) {
        console.log('Cookie banner found, clicking...');
        await cookieButton.click();
        await sleep(randomDelay(1500, 2500));
      } else {
        console.log('No cookie banner found.');
      }
    } catch (e) {
      console.log('Could not click cookie banner, continuing...');
    }
    
    // Ga nu naar de daadwerkelijke productpagina
    console.log(`Navigating to product page: ${url}`);
    await page.goto(url, { waitUntil: 'networkidle2' });

    // --- PRIJS ZOEKEN ---
    const salePriceXPath = "//*[@id='start-of-content']/div[1]/div/div/div/div/article/div/div/div[2]/div[2]/div[1]/div[2]/span[1]";
    const regularPriceXPath = "//*[@id='start-of-content']/div[1]/div/div/div/div/article/div/div/div[2]/div[2]/div[1]/div/span[1]";
    let ariaLabel = null;
    
    let [element] = await page.$x(salePriceXPath);
    if(element) {
        ariaLabel = await page.evaluate(el => el.getAttribute('aria-label'), element);
    }
    
    if(!ariaLabel) {
        [element] = await page.$x(regularPriceXPath);
        if(element) {
            ariaLabel = await page.evaluate(el => el.getAttribute('aria-label'), element);
        }
    }

    if (ariaLabel) {
      const match = ariaLabel.match(/€\s*([0-9,.]+)/);
      if (match && match[1]) {
        let priceStr = match[1].replace(/\./g, '').replace(/,/g, '.');
        return { price: parseFloat(priceStr), currency: 'EUR' };
      } else {
        return { error: `Could not parse price from aria-label: '${ariaLabel}'` };
      }
    } else {
      await page.screenshot({ path: `/home/scrape/mealflow-scraper/logs/ah_error_screenshot_${Date.now()}.png` });
      return { error: 'Price element not found for AH. Screenshot taken.' };
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