// mealflow-scraper/server.js
const express = require('express');
const { scrapeAh } = require('./ah_scraper');
// Voeg hier later je jumbo_scraper etc. toe
// const { scrapeJumbo } = require('./jumbo_scraper');

const app = express();
app.use(express.json()); // Middleware om JSON-requests te parsen

const port = 8000;

const SCRAPER_MAPPING = {
  "Albert Heijn": scrapeAh,
  // "Jumbo": scrapeJumbo,
};

app.post('/scrape', async (req, res) => {
  const { supermarket, url } = req.body;

  if (!supermarket || !url) {
    return res.status(400).json({ error: 'Missing supermarket or url in request body' });
  }
  
  const scraperFunction = SCRAPER_MAPPING[supermarket];

  if (!scraperFunction) {
    return res.status(400).json({ error: `No scraper configured for supermarket: ${supermarket}` });
  }
 
  console.log(`Received request for ${supermarket}: ${url}`);

  try {
    const result = await scraperFunction(url);
    if (result.error) {
      // 422 Unprocessable Entity: de request was goed, maar de inhoud kon niet verwerkt worden
      console.error(`Scraping failed for ${url}: ${result.error}`);
      return res.status(422).json(result);
    }
    // 200 OK: succes
    console.log(`Scraping successful for ${url}:`, result);
    return res.status(200).json(result);
  } catch (e) {
    // 500 Internal Server Error: er is iets onverwachts misgegaan
    console.error('A critical error occurred:', e);
    return res.status(500).json({ error: 'An internal server error occurred.' });
  }
});

app.listen(port, '0.0.0.0', () => {
  console.log(`Node.js Scraper API is running on http://0.0.0.0:${port}`);
});