#!/bin/bash
set -e

# --- Configuratie ---
GIT_REPO_URL="https://github.com/sjemmeh/Scraper.git"
PROJECT_DIR="/home/scrape/mealflow-scraper" 
USERNAME="scrape" # 

echo "--- Stap 1: Systeem updaten en basispakketten installeren ---"
sudo apt-get update
sudo apt-get install -y git python3 python3-pip python3-venv wget unzip curl jq

echo "--- Stap 2: Google Chrome installeren ---"
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install -y ./google-chrome-stable_current_amd64.deb
rm google-chrome-stable_current_amd64.deb
echo "Google Chrome geïnstalleerd."

echo "--- Stap 3: ChromeDriver installeren (automatische versie-detectie) ---"
# Haal de geïnstalleerde Chrome versie op
CHROME_VERSION=$(google-chrome --product-version | cut -d. -f1)
echo "Gedetecteerde Chrome-versie (major): $CHROME_VERSION"

# Haal de nieuwste bekende goede ChromeDriver versie op die overeenkomt met de major Chrome versie
LAST_KNOWN_GOOD_VERSION=$(curl -s "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json" | jq -r ".channels.Stable.downloads.chromedriver[] | select(.platform==\"linux64\") | .url")

if [ -z "$LAST_KNOWN_GOOD_VERSION" ]; then
    echo "Kon de juiste ChromeDriver versie niet automatisch vinden. Script stopt."
    exit 1
fi

echo "ChromeDriver downloaden van: $LAST_KNOWN_GOOD_VERSION"
wget -O chromedriver.zip "$LAST_KNOWN_GOOD_VERSION"
unzip chromedriver.zip

sudo mv chromedriver-linux64/chromedriver /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver
rm chromedriver.zip
rm -rf chromedriver-linux64/
echo "ChromeDriver geïnstalleerd en geconfigureerd."

echo "--- Stap 4: Project repository klonen ---"
if [ -d "$PROJECT_DIR" ]; then
    echo "Projectdirectory bestaat al. Bestaande directory wordt overgeslagen."
else
    git clone "$GIT_REPO_URL" "$PROJECT_DIR"
    sudo chown -R $USERNAME:$USERNAME "$PROJECT_DIR"
fi
cd "$PROJECT_DIR"

echo "--- Stap 5: Python virtuele omgeving opzetten en dependencies installeren ---"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate

pip install -r requirements.txt
deactivate

echo "--- Installatie voltooid! ---"
echo "Navigeer nu naar de projectmap: cd $PROJECT_DIR"
echo "Maak de services aan en start ze met: ./start.sh"