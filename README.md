# WebWG — REST API для управления WireGuard VPN

**WebWG** — это лёгкий и удобный REST API-сервис для автоматизации управления VPN‑сервером на базе WireGuard. Сервис позволяет в несколько команд добавлять и удалять пользователей, генерировать конфигурации и отслеживать статус подключений.

## 🎯 Основные возможности

- Управление пир‑узлами: создание, редактирование и удаление  
- Генерация ключей и клиентских конфигураций (`.conf`)  
- Автоматическая «горячая» синхронизация изменений (`wg syncconf`)  
- Получение статистики подключений (через `wg show`)  
- Генерация QR‑кодов для быстрого подключения мобильных клиентов  
- Простая интеграция с внешними скриптами и системными командами

## 🛠️ Технологии

- **Python 3.10+**  
- **FastAPI** — разработка REST API  
- **Uvicorn** — ASGI‑сервер  
- **subprocess** — вызов команд `wg`, `wg-quick`, `systemctl`  
- **qrcode** — генерация QR‑кодов  
- **HTML/CSS/JavaScript** — лёгкий веб‑фронтенд  
- **JSON** — хранилище конфигураций (`peers.json`)  
- **systemd** — автозапуск сервиса

## 📂 Структура проекта

- `webwg/`
  - `main.py`                 — точка входа FastAPI
  - `wg.py`                   — логика работы с WireGuard
  - `schemas.py`              — Pydantic‑модели
  - `peers.json`              — JSON‑хранилище конфигураций
  - `users/`                  — папка с клиентскими `.conf`‑файлами
  - `static/`                 — статика (QR‑коды и т.д.)
  - `templates/`              — шаблоны конфигураций WireGuard
  - `webwg.service`           — unit‑файл systemd
  - `requirements.txt`        — список Python‑зависимостей
  - `README.md`               — этот файл

## 🚀 Установка и запуск

1. Клонировать репозиторий и перейти в каталог проекта:
```bash
git clone https://github.com/wepmaner/webwg.git
cd webwg
```
2. Создать и активировать виртуальное окружение:
```bash
python3 -m venv .venv
source .venv/bin/activate
```
3. Установить зависимости:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```
4. Подготовить конфиг WireGuard (/etc/wireguard/wg0.conf) и JSON‑хранилище (peers.json).
5. Запустить сервис в режиме разработки:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```
6. Для автозапуска создать unit‑файл webwg.service и включить его:
```
sudo cp webwg.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now webwg.service
```
## ⚙️ Использование API

- POST /api/users — добавить нового пира
- GET /api/users — получить список пиров
- PUT /api/users/{username} — обновить параметры пира
- DELETE /api/users/{username} — удалить пира
- GET /api/getInfo — получить текущее состояние VPN
- GET /api/users/{username}/qrcode — получить QR‑код

(Подробная документация доступна в автоматически сгенерированном Swagger UI: http://<host>:8000/docs)
