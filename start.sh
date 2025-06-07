#!/bin/bash
set -e

echo "--- Scraper Service Setup ---"

# Huidige map van het script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
SERVICE_FILES_DIR="$SCRIPT_DIR/services"

echo "Kopiëren van service-bestanden naar /etc/systemd/system/..."
sudo cp "$SERVICE_FILES_DIR/chrome-debug.service" /etc/systemd/system/
sudo cp "$SERVICE_FILES_DIR/scraper-api.service" /etc/systemd/system/

echo "Systemd herladen om nieuwe services te detecteren..."
sudo systemctl daemon-reload

echo "Services activeren (starten automatisch bij opstarten van de VM)..."
sudo systemctl enable chrome-debug.service
sudo systemctl enable scraper-api.service

echo "Services (her)starten..."
sudo systemctl restart chrome-debug.service
sudo systemctl restart scraper-api.service

echo "Setup voltooid!"
echo ""
echo "Controleer de status van de services met:"
echo "sudo systemctl status chrome-debug.service"
echo "sudo systemctl status scraper-api.service"
echo ""
echo "Bekijk live logs met:"
echo "sudo journalctl -u chrome-debug.service -f"
echo "sudo journalctl -u scraper-api.service -f"