#!/bin/bash
# Zorgt ervoor dat het script stopt als er een fout optreedt
set -e

# --- Configuratie ---
# Pas deze waarden aan indien nodig voor een nieuwe gebruiker of locatie
GIT_REPO_URL="https://github.com/sjemmeh/Scraper.git"
USERNAME="scrape"
PROJECT_DIR="/home/${USERNAME}/mealflow-scraper"

echo "--- Stap 1: Systeem updaten en basispakketten installeren ---"
sudo apt-get update
sudo apt-get install -y git python3 python3-pip python3-venv wget unzip curl jq

echo "--- Stap 2: Google Chrome installeren ---"
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install -y ./google-chrome-stable_current_amd64.deb || sudo apt --fix-broken install -y
rm google-chrome-stable_current_amd64.deb
echo "Google Chrome geïnstalleerd."

echo "--- Stap 3: ChromeDriver installeren (automatische versie-detectie) ---"
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
echo "ChromeDriver geïnstalleerd."

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

echo "--- Stap 6: Scripts en service-bestand dynamisch aanmaken ---"

# Maak de services map aan
mkdir -p "${PROJECT_DIR}/services"

# Genereer start_chrome.sh
echo "Genereer start_chrome.sh..."
cat << EOF > "${PROJECT_DIR}/start_chrome.sh"
#!/bin/bash
echo "Chrome starten met remote debugging op poort 9222..."
/usr/bin/google-chrome \\
    --remote-debugging-port=9222 \\
    --user-data-dir="/home/${USERNAME}/.config/google-chrome/ScraperProfile" \\
    --no-first-run \\
    --no-sandbox
EOF

# Genereer scraper-api.service
echo "Genereer services/scraper-api.service..."
cat << EOF > "${PROJECT_DIR}/services/scraper-api.service"
[Unit]
Description=MealFlow Scraper API Service
After=network.target

[Service]
User=${USERNAME}
Group=${USERNAME}
WorkingDirectory=${PROJECT_DIR}
ExecStart=${PROJECT_DIR}/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Genereer start.sh
echo "Genereer start.sh (voor het beheren van de API service)..."
cat << EOF > "${PROJECT_DIR}/start.sh"
#!/bin/bash
set -e

echo "--- Scraper API Service Setup ---"

# Kopieer de service file naar de systemd directory
echo "Kopiëren van scraper-api.service naar /etc/systemd/system/..."
sudo cp "${PROJECT_DIR}/services/scraper-api.service" /etc/systemd/system/

# Herlaad systemd en activeer/herstart de service
echo "Systemd herladen..."
sudo systemctl daemon-reload
echo "Scraper API service activeren (start automatisch bij opstarten)..."
sudo systemctl enable scraper-api.service
echo "Scraper API service (her)starten..."
sudo systemctl restart scraper-api.service

echo ""
echo "Setup van de API service is voltooid!"
echo "Controleer de status met: sudo systemctl status scraper-api.service"
EOF

# Maak de scripts uitvoerbaar
chmod +x "${PROJECT_DIR}/start_chrome.sh"
chmod +x "${PROJECT_DIR}/start.sh"

echo "--- Installatie voltooid! ---"
echo "Navigeer nu naar de projectmap: cd ${PROJECT_DIR}"
echo "Om de scraper te gebruiken:"
echo "1. Start Chrome in een terminal met: ./start_chrome.sh"
echo "2. Start de API service in een andere terminal met: ./start.sh"
echo "   (Let op: ./start.sh hoef je maar één keer te draaien. Daarna kun je de service beheren met 'sudo systemctl [start|stop|restart] scraper-api.service')"