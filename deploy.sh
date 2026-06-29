#!/bin/bash

# Скрипт автоматического развертывания NortGru на Ubuntu VPS
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}==============================================${NC}"
echo -e "${GREEN}          Развертывание NortGru на VPS        ${NC}"
echo -e "${GREEN}==============================================${NC}"

# 1. Проверка Docker
if ! [ -x "$(command -v docker)" ]; then
    echo -e "${YELLOW}[!] Docker не установлен. Установка Docker...${NC}"
    sudo apt-get update
    sudo apt-get install -y curl
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo -e "${GREEN}[+] Docker успешно установлен!${NC}"
else
    echo -e "${GREEN}[+] Docker уже установлен.${NC}"
fi

# 2. Проверка Docker Compose
if ! docker compose version >/dev/null 2>&1; then
    echo -e "${YELLOW}[!] Docker Compose v2 не найден. Установка плагина docker-compose-plugin...${NC}"
    sudo apt-get update
    sudo apt-get install -y docker-compose-plugin
    echo -e "${GREEN}[+] Docker Compose успешно установлен!${NC}"
else
    echo -e "${GREEN}[+] Docker Compose уже установлен.${NC}"
fi

# 3. Настройка файла .env
if [ ! -f .env ]; then
    echo -e "${YELLOW}[!] Файл .env не найден. Создаю его из .env.example...${NC}"
    cp .env.example .env
    echo -e "${GREEN}[+] Файл .env успешно создан.${NC}"
    echo -e "${YELLOW}[!] ВНИМАНИЕ: Обязательно отредактируйте файл .env (команда: nano .env) перед запуском, если требуется ввести реальные пароли или адреса 1С/Ollama.${NC}"
    
    read -p "Хотите продолжить запуск прямо сейчас с настройками по умолчанию? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}[*] Развертывание приостановлено. Пожалуйста, настройте .env и запустите скрипт снова: ./deploy.sh${NC}"
        exit 0
    fi
else
    echo -e "${GREEN}[+] Файл .env уже настроен.${NC}"
fi

# 4. Запуск контейнеров
echo -e "${GREEN}[*] Запуск сборки и развертывания контейнеров...${NC}"
sudo docker compose down --remove-orphans || true
sudo docker compose up --build -d

# 5. Очистка неиспользуемых ресурсов (экономия места на VPS)
echo -e "${GREEN}[*] Очистка старых неиспользуемых Docker-образов и кэша сборщика...${NC}"
sudo docker image prune -f || true
sudo docker builder prune -f || true

echo -e "${GREEN}==============================================${NC}"
echo -e "${GREEN}    Приложение NortGru успешно запущено!      ${NC}"
echo -e "${GREEN}==============================================${NC}"
echo -e "Фронтенд доступен на порту: ${YELLOW}http://<IP_вашего_VPS>:80${NC}"
echo -e "Бэкенд доступен на порту:   ${YELLOW}http://<IP_вашего_VPS>:8000/api${NC}"
echo -e "Документация API (Swagger): ${YELLOW}http://<IP_вашего_VPS>:8000/api/docs${NC}"
echo -e ""
echo -e "Для просмотра логов в реальном времени используйте команду:"
echo -e "${YELLOW}docker compose logs -f${NC}"
echo -e "=============================================="
