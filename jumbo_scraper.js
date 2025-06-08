const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());

// Functie voor een willekeurige vertraging
const sleep = (ms) => new Promise(res => setTimeout(res, ms));
const randomDelay = (min, max) => Math.random() * (max - min) + min;

const scrapeJumbo = async (url) => {
  let browser = null;
  console.log('Starting Jumbo scrape with Puppeteer-Stealth...');
  try {
    browser = await puppeteer.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--window-size=1920,1080']
    });

    const page = await browser.newPage();
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36');

    console.log(`Navigating to product page: ${url}`);
    await page.goto(url, { waitUntil: 'networkidle2' });

    // Probeer de cookie banner te accepteren
    try {
      const cookieButtonXPath = "xpath/" + "//button[contains(., 'Accepteren')]";
      const cookieButton = await page.waitForSelector(cookieButtonXPath, { timeout: 5000 });
      if (cookieButton) {
        console.log('Jumbo cookie banner found, clicking...');
        await cookieButton.click();
        await sleep(randomDelay(1000, 2000));
      }
    } catch (e) {
      console.log('No Jumbo cookie banner found or could not click.');
    }

    // XPaths voor Jumbo
    const salePriceXPath = `xpath/${'//*[@id="mainContent"]/div[2]/div/div[2]/div[1]/div[2]/div[2]/div[2]/div'}`;
    const regularPriceXPath = `xpath/${'//*[@id="mainContent"]/div[2]/div/div[2]/div[1]/div[2]/div[2]/div[1]/div'}`;
    let priceText = null;
    
    // Probeer eerst de aanbiedingsprijs te vinden
    try {
      const saleElement = await page.waitForSelector(salePriceXPath, { timeout: 3000 });
      const text = await page.evaluate(el => el.textContent, saleElement);
      if (text && text.includes('Nieuwe prijs:')) {
        priceText = text;
      }
    } catch (e) {
      console.log('Sale price element not found, trying regular price...');
    }

    // Als er geen geldige aanbiedingsprijs is gevonden, probeer de normale prijs
    if (!priceText) {
      try {
        const regularElement = await page.waitForSelector(regularPriceXPath, { timeout: 3000 });
        const text = await page.evaluate(el => el.textContent, regularElement);
        if (text && text.includes('Prijs:')) {
          priceText = text;
        }
      } catch (e) {
        console.log('Regular price element also not found.');
      }
    }
    
    if (priceText) {
      const match = priceText.match(/€\s*([0-9,.]+)/);
      if (match && match[1]) {
        let priceStr = match[1].replace(/\./g, '').replace(/,/g, '.');
        return { price: parseFloat(priceStr), currency: 'EUR' };
      } else {
        return { error: `Could not parse price from text: '${priceText}'` };
      }
    } else {
      const screenshotPath = `/home/scrape/mealflow-scraper/logs/jumbo_error_screenshot_${Date.now()}.png`;
      await page.screenshot({ path: screenshotPath });
      return { error: `Valid price element not found for Jumbo. Screenshot taken at ${screenshotPath}.` };
    }

  } catch (e) {
    console.error('An unexpected error occurred in scrapeJumbo:', e);
    return { error: e.message };
  } finally {
    if (browser) {
      await browser.close();
      console.log('Browser closed.');
    }
  }
};

module.exports = { scrapeJumbo };