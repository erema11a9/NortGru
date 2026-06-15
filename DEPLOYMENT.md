# Руководство по развертыванию NortGru на Ubuntu VPS через Docker

Данный документ содержит пошаговую инструкцию по установке и настройке корпоративного личного кабинета **NortGru** на сервере под управлением Ubuntu (20.04 / 22.04 / 24.04 LTS).

---

## Содержание
1. [Подготовка VPS сервера](#1-подготовка-vps-сервера)
2. [Подключение GitHub к VPS](#2-подключение-github-к-vps)
3. [Развертывание проекта](#3-развертывание-проекта)
4. [Настройка переменных окружения (.env)](#4-настройка-переменных-окружения-env)
5. [Интеграция с Ollama на хост-машине](#5-интеграция-с-ollama-на-хост-машине)
6. [Полезные команды для управления](#6-полезные-команды-для-управления)
7. [Решение проблем с блокировкой Docker Hub в России](#7-решение-проблем-с-блокировкой-docker-hub-в-россии)

---

## 1. Подготовка VPS сервера

Перед установкой проекта обновите список пакетов и настройте файрвол для безопасности:

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Настройка брандмауэра UFW (открываем нужные порты)
sudo ufw allow 22/tcp       # SSH
sudo ufw allow 80/tcp       # HTTP (Веб-интерфейс)
sudo ufw allow 443/tcp      # HTTPS (если будете настраивать SSL)

# Включение файрвола (введите 'y' для подтверждения)
sudo ufw enable
```

---

## 2. Подключение GitHub к VPS

Для безопасного и быстрого переноса кода с GitHub на сервер рекомендуется использовать SSH-ключи.

1. **Сгенерируйте новый SSH-ключ на VPS**:
   ```bash
   ssh-keygen -t ed25519 -C "your_email@example.com"
   ```
   *(Нажмите Enter несколько раз, чтобы оставить путь по умолчанию без пароля)*

2. **Выведите публичный ключ в консоль и скопируйте его**:
   ```bash
   cat ~/.ssh/id_ed25519.pub
   ```

3. **Добавьте ключ в GitHub**:
   - Перейдите в ваш репозиторий NortGru на GitHub.
   - Откройте **Settings** -> **Deploy keys** -> **Add deploy key**.
   - Вставьте скопированный ключ, дайте ему название (например, `VPS Ubuntu`) и нажмите **Add key**.

4. **Клонируйте репозиторий на VPS**:
   ```bash
   git clone git@github.com:ВАШ_АККАУНТ/NortGru.git
   cd NortGru
   ```

---

## 3. Развертывание проекта

Мы подготовили скрипт `deploy.sh`, который сделает всю рутинную работу за вас:
- Проверит и установит Docker и Docker Compose.
- Скопирует конфигурационный файл `.env.example` в рабочий `.env`.
- Сформирует образы и запустит базу данных PostgreSQL, бэкенд на FastAPI и фронтенд на Vue через Nginx.
- Очистит устаревшие неиспользуемые Docker-образы для экономии диска.

1. **Сделайте скрипт исполняемым**:
   ```bash
   chmod +x deploy.sh
   ```

2. **Запустите развертывание**:
   ```bash
   ./deploy.sh
   ```

> [!NOTE]
> Скрипт спросит, хотите ли вы продолжить запуск с настройками по умолчанию, если создался новый файл `.env`. Если вам нужно настроить подключение к реальной 1С или Ollama, нажмите `n` (нет), отредактируйте `.env` через `nano .env`, а затем запустите `./deploy.sh` повторно.

---

## 4. Настройка переменных окружения (.env)

Файл `.env` в корне проекта управляет всеми настройками соединения. 

```ini
# --- Параметры СУБД PostgreSQL ---
POSTGRES_USER=postgres
POSTGRES_PASSWORD=12393qwe     # <-- Смените этот пароль в продакшене!
POSTGRES_DB=nortgru_db

# --- Параметры подключения к Ollama (нейросеть) ---
# На Linux-хосте docker перенаправит host.docker.internal на вашу VPS-машину
OLLAMA_URL=http://host.docker.internal:11434/api/chat
OLLAMA_MODEL=gemma4:e4b

# --- Параметры подключения к публикации 1С ---
ONEC_BASE_URL=http://host.docker.internal:8081/InfoBase4/hs/edu-agent
ONEC_USER=admin
ONEC_PASSWORD=PASSWORD
```

---

## 5. Интеграция с Ollama на хост-машине

Если вы хотите запустить Ollama прямо на вашей VPS (чтобы использовать GPU или CPU сервера), выполните следующие шаги:

1. **Установите Ollama на сервер**:
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ```

2. **Разрешите подключения из Docker-контейнеров**:
   По умолчанию Ollama на Linux слушает только `127.0.0.1`. Чтобы Docker-контейнер бэкенда мог до неё достучаться через `host.docker.internal`, настройте ее запуск на адресе `0.0.0.0`:
   
   Откройте настройки службы через systemd:
   ```bash
   sudo systemctl edit ollama.service
   ```
   В открывшемся текстовом редакторе вставьте блок строго между комментариями:
   ```ini
   [Service]
   Environment="OLLAMA_HOST=0.0.0.0"
   ```
   Сохраните файл (в Nano: `Ctrl+O` -> `Enter` -> `Ctrl+X`).

3. **Перезапустите Ollama**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart ollama
   ```

4. **Скачайте нужную модель** (например, `gemma4:e4b` или другую):
   ```bash
   ollama run gemma4:e4b
   ```
   *(После скачивания модели можно выйти из консоли модели через Ctrl+D)*

---

## 6. Полезные команды для управления

Все команды необходимо выполнять, находясь в корневой папке `/NortGru`:

* **Просмотр логов в реальном времени**:
  ```bash
  docker compose logs -f
  ```
  *(Для просмотра логов конкретного сервиса, например бэкенда: `docker compose logs -f backend`)*

* **Остановка приложения**:
  ```bash
  docker compose down
  ```

* **Перезапуск контейнеров с пересборкой**:
  ```bash
  docker compose up --build -d
  ```

* **Подключение к базе данных PostgreSQL внутри контейнера**:
  ```bash
  docker exec -it nortgru-db psql -U postgres -d nortgru_db
  ```

* **Проверка статуса запущенных контейнеров**:
  ```bash
  docker compose ps
  ```

---

## 7. Решение проблем с блокировкой Docker Hub в России

Если при сборке (`docker compose up --build -d`) вы получаете ошибку:
> `Error response from daemon: failed to resolve reference "docker.io/library/...": failed to do request: Head "...": net/http: TLS handshake timeout`
или
> `Error response from daemon: ... 403 Forbidden`

Это связано с тем, что Docker Hub ограничивает скачивание образов для российских IP-адресов или соединение блокируется DPI.

### Решение: Настройка локальных зеркал (Registry Mirrors)

Для того чтобы Docker скачивал базовые образы (например, `postgres` и `node`) через рабочие российские зеркала, настройте конфигурационный файл Docker:

1. **Откройте или создайте файл конфигурации Docker**:
   ```bash
   sudo nano /etc/docker/daemon.json
   ```

2. **Вставьте следующее содержимое** (список работающих зеркал от GitVerse, Beget и TimeWeb):
   ```json
   {
     "registry-mirrors": [
       "https://dh-mirror.gitverse.ru",
       "https://dockerhub.timeweb.cloud",
       "https://dockerhub1.beget.com",
       "https://mirror.gcr.io"
     ]
   }
   ```
   *(Если в файле уже есть какие-то настройки, добавьте `registry-mirrors` через запятую в общий JSON-объект)*

3. **Сохраните изменения**:
   Нажмите `Ctrl+O` -> `Enter` -> `Ctrl+X` для выхода из Nano.

4. **Перезапустите демон Docker**, чтобы применить настройки:
   ```bash
   sudo systemctl restart docker
   ```

5. **Повторите команду сборки**:
   ```bash
   docker compose up -d --build
   ```
   После этого образы успешно скачаются без сетевых ошибок.


---

## 8. Настройка домена и SSL (HTTPS)

Для того чтобы проект работал по вашему домену (например, `nortgru.ru`) и использовал защищенное соединение HTTPS, выполните следующие шаги.

### Шаг 1: Направьте домен на IP-адрес сервера (DNS)
В панели управления вашего регистратора домена (Reg.ru, Nic.ru, TimeWeb, Namecheap и др.) перейдите в настройки DNS и добавьте записи:
1. **A-запись**:
   - Имя хоста (Host/Name): `@` (или оставьте пустым)
   - IP-адрес (Value/Points to): `IP_адрес_вашего_VPS`
2. **CNAME-запись** (для поддержки `www`):
   - Имя хоста (Host/Name): `www`
   - Значение (Value/Points to): `nortgru.ru`

> [!NOTE]
> Обновление DNS-записей у провайдеров интернета по всему миру может занять от 10 минут до нескольких часов.

---

### Вариант А: Использование Cloudflare (Самый простой и быстрый способ)
Если вы настроите домен через Cloudflare (пропишете NS-сервера Cloudflare в панели домена):
1. В панели DNS Cloudflare добавьте **A-запись** с вашим IP-адресом и убедитесь, что включен переключатель **Proxy status** (оранжевое облако).
2. Перейдите в раздел **SSL/TLS** -> **Overview** и выберите режим **Flexible** (или **Full**, если на сервере настроен самоподписанный сертификат).
3. В этом случае Cloudflare автоматически выдаст HTTPS-сертификат для пользователей. Вам **не нужно** менять настройки Nginx или порты на сервере, так как Docker продолжает работать на 80 порту, а Cloudflare принимает HTTPS и проксирует его на ваш сервер.

---

### Вариант Б: Настройка SSL на сервере через Certbot и Host Nginx (Рекомендуемый стандартный способ)
Если вы хотите выпускать сертификаты Let's Encrypt прямо на сервере без сторонних прокси-сервисов:

#### 1. Освободите порт 80 для системного Nginx
По умолчанию Docker-контейнер фронтенда занимает порт 80. Нам нужно освободить его, чтобы Nginx на хост-машине мог принимать запросы и направлять их в Docker.

В файле `docker-compose.yml` измените порты для `frontend`:
```yaml
  frontend:
    ...
    ports:
      - "8080:80"  # Изменили с "80:80" на "8080:80"
```

#### 2. Установите Nginx и Certbot на VPS
```bash
sudo apt update
sudo apt install nginx certbot python3-certbot-nginx -y
```

#### 3. Настройте конфигурационный файл Nginx
Создайте новый конфигурационный файл:
```bash
sudo nano /etc/nginx/sites-available/nortgru
```
Вставьте конфигурацию:
```nginx
server {
    listen 80;
    server_name nortgru.ru www.nortgru.ru;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
Активируйте конфигурацию и перезапустите Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/nortgru /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 4. Получите SSL сертификат Let's Encrypt
Запустите Certbot для автоматического выпуска сертификата:
```bash
sudo certbot --nginx -d nortgru.ru -d www.nortgru.ru
```
*Certbot сам настроит защищенное HTTPS-соединение и автоматический редирект с HTTP на HTTPS.*

---

### Шаг 2: Настройка CORS в `.env` (Критически важно)
Поскольку бэкенд на FastAPI защищает запросы с помощью CORS, необходимо добавить ваш новый домен в разрешенные источники.

Откройте файл `.env` на сервере и обновите переменную `ALLOWED_ORIGINS`, добавив туда ваш домен (с протоколами `http` и `https`):
```ini
ALLOWED_ORIGINS=https://nortgru.ru,https://www.nortgru.ru,http://localhost,http://localhost:80
```

После редактирования `.env` и `docker-compose.yml` перезапустите контейнеры:
```bash
docker compose down
docker compose up -d --build
```


