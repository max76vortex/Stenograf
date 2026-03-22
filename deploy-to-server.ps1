# Деплой N8N-projects на сервер
# Использование: .\deploy-to-server.ps1 -ServerUser "root" -ServerHost "n8n.maxvortex.ru"
# или: $env:SERVER="user@n8n.maxvortex.ru"; .\deploy-to-server.ps1

param(
    [string]$ServerUser = "root",
    [string]$ServerHost = "n8n.maxvortex.ru",
    [string]$RemotePath = "/root/N8N-projects"
)

$Server = "${ServerUser}@${ServerHost}"
$LocalPath = $PSScriptRoot

Write-Host "=== Копирование файлов на $Server ===" -ForegroundColor Cyan
scp -r "$LocalPath\docker-compose.yml" "$LocalPath\.env" "$LocalPath\nginx" "$LocalPath\server-setup.sh" "${Server}:${RemotePath}/"

Write-Host "`n=== Запуск на сервере ===" -ForegroundColor Cyan
ssh $Server "cd $RemotePath && docker compose up -d"

Write-Host "`nГотово. Проверьте: https://n8n.maxvortex.ru" -ForegroundColor Green
Write-Host "Не забудьте настроить Nginx и DNS!" -ForegroundColor Yellow
