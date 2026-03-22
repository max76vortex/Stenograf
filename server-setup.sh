#!/bin/bash
# Установка n8n на сервере (Linux)
# Запуск: bash server-setup.sh

set -e

echo "=== Установка Docker (если не установлен) ==="
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
    echo "Docker установлен. Перелогиньтесь для доступа к docker без sudo."
else
    echo "Docker уже установлен."
fi

echo ""
echo "=== Запуск n8n ==="
docker compose up -d

echo ""
echo "=== Статус ==="
docker compose ps

echo ""
echo "n8n запущен на порту 5678 (localhost)."
echo "Настройте Nginx/Caddy для n8n.maxvortex.ru -> http://127.0.0.1:5678"
echo "Используйте конфиг из папки nginx/"
