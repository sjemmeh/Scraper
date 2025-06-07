#!/bin/bash
set -e

echo "--- Scraper API Service Setup ---"

# Huidige map van het script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
SERVICE_FILES_DIR="$SCRIPT_DIR/services"

echo "Kopiëren van scraper-api.service naar /etc/systemd/system/..."
sudo cp "$SERVICE_FILES_DIR/scraper-api.service" /etc/systemd/system/

echo "Systemd herladen om nieuwe service te detecteren..."
sudo systemctl daemon-reload

echo "Scraper API service activeren (start automatisch bij opstarten van de VM)..."
sudo systemctl enable scraper-api.service

echo "Scraper API service (her)starten..."
sudo systemctl restart scraper-api.service

echo "Setup voltooid!"
echo ""
echo "Controleer de status van de service met:"
echo "sudo systemctl status scraper-api.service"
echo ""
echo "Bekijk live logs met:"
echo "sudo journalctl -u scraper-api.service -f"
echo ""
echo "BELANGRIJK: Vergeet niet om Chrome handmatig te starten in een aparte terminal!"