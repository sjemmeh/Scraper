#!/bin/bash
# Zorgt ervoor dat het script stopt als er een fout optreedt
set -e

# --- Configuratie ---
# Pas deze waarden aan indien nodig voor een nieuwe gebruiker of locatie
GIT_REPO_URL="https://github.com/sjemmeh/Scraper.git"
USERNAME="scrape"
GIT_BRANCH="main" # Pas aan als je een andere branch gebruikt
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
    echo "Projectdirectory bestaat al. Updaten van de repo..."
    cd "$PROJECT_DIR"
    git fetch origin
    git reset --hard "origin/${GIT_BRANCH}"
else
    git clone "$GIT_REPO_URL" "$PROJECT_DIR"
fi
sudo chown -R $USERNAME:$USERNAME "$PROJECT_DIR"
cd "$PROJECT_DIR"

echo "--- Stap 5: Python virtuele omgeving opzetten en dependencies installeren ---"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt
deactivate

echo "--- Stap 6: Scripts en service-bestand dynamisch aanmaken ---"
# Maak benodigde mappen aan als de gebruiker 'scrape'
sudo -u ${USERNAME} mkdir -p "${PROJECT_DIR}/services"
sudo -u ${USERNAME} mkdir -p "${PROJECT_DIR}/logs"
sudo -u ${USERNAME} touch "${PROJECT_DIR}/logs/cron.log"


# Genereer start_chrome.sh
echo "Genereer start_chrome.sh..."
sudo -u ${USERNAME} tee "${PROJECT_DIR}/start_chrome.sh" > /dev/null << EOF
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
sudo -u ${USERNAME} tee "${PROJECT_DIR}/services/scraper-api.service" > /dev/null << EOF
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

# Genereer start.sh (voor het beheren van de API service)
echo "Genereer start.sh (voor het beheren van de API service)..."
sudo -u ${USERNAME} tee "${PROJECT_DIR}/start.sh" > /dev/null << EOF
#!/bin/bash
set -e
echo "--- Scraper API Service Setup ---"
echo "Kopiëren van scraper-api.service naar /etc/systemd/system/..."
sudo cp "${PROJECT_DIR}/services/scraper-api.service" /etc/systemd/system/
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

# --- NIEUWE SECTIE ---
echo "--- Stap 7: Auto-update script en cron job instellen ---"

# Genereer auto_update.sh
echo "Genereer auto_update.sh..."
sudo -u ${USERNAME} tee "${PROJECT_DIR}/auto_update.sh" > /dev/null << EOF
#!/bin/bash
# Dit script wordt elke 15 minuten door cron uitgevoerd om de scraper up-to-date te houden.

# Ga naar de projectdirectory
cd "${PROJECT_DIR}" || { echo "Project directory niet gevonden"; exit 1; }

echo "--- Auto-Update Script Gestart: \$(date) ---"

# Haal laatste info op van de remote
git fetch

LOCAL=\$(git rev-parse HEAD)
REMOTE=\$(git rev-parse "origin/${GIT_BRANCH}")

if [ "\$LOCAL" = "\$REMOTE" ]; then
    echo "Geen nieuwe updates gevonden."
else
    echo "Nieuwe update gevonden! Starten van het update-proces..."
    git reset --hard "origin/${GIT_BRANCH}" && git clean -fd
    echo "Code bijgewerkt."
    
    echo "Python dependencies installeren/updaten..."
    source "${PROJECT_DIR}/venv/bin/activate"
    pip install -r requirements.txt
    deactivate
    
    echo "Herstarten van de scraper-api service..."
    sudo systemctl restart scraper-api.service
    echo "Update succesvol voltooid op \$(date)"
fi
echo "--- Auto-Update Script Klaar ---"
EOF

# Maak alle scripts uitvoerbaar
chmod +x "${PROJECT_DIR}/start_chrome.sh"
chmod +x "${PROJECT_DIR}/start.sh"
chmod +x "${PROJECT_DIR}/auto_update.sh"

# Maak het cron job bestand direct aan in /etc/cron.d/
CRON_JOB_FILE="/etc/cron.d/mealflow-scraper-updater"
CRON_SCHEDULE="*/15 * * * *" # Elke 15 minuten

echo "Aanmaken van cron job in ${CRON_JOB_FILE}..."
sudo tee "$CRON_JOB_FILE" > /dev/null << EOF
# Automatische update voor de MealFlow scraper
${CRON_SCHEDULE} ${USERNAME} ${PROJECT_DIR}/auto_update.sh >> ${PROJECT_DIR}/logs/cron.log 2>&1
EOF

# Zet de juiste permissies op het cron-bestand
sudo chmod 644 "$CRON_JOB_FILE"

echo "Cron job succesvol aangemaakt."

# --- Laatste stap ---
echo "--- Stap 8: De services voor de eerste keer starten ---"
# Draai het start-script om de API service te kopiëren en te starten
bash "${PROJECT_DIR}/start.sh"

echo ""
echo "--- VOLLEDIGE INSTALLATIE VOLTOOID! ---"
echo "De scraper API draait nu als een service en zal zichzelf elke 15 minuten updaten."
echo "Je hoeft alleen nog maar Chrome handmatig te starten met: ./start_chrome.sh"