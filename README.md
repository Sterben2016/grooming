# 🐾 Grooming Bot

Телеграм-бот для записи на груминг животных.
Стек: **Python 3.11+, aiogram 3, SQLAlchemy (async) + SQLite, aiohttp**.

## Возможности

**Клиент:**
- Регистрация (имя + телефон через кнопку "отправить контакт")
- Запись: выбор мастера → услуги (если есть) → даты → свободного времени → подтверждение
- «Мои записи» — список активных записей с отменой
- Раздел «О нас»

**Администратор** (id из `ADMIN_IDS`), команда `/admin`:
- 👨‍🔧 Мастера — добавление (имя, рабочие дни, часы работы, длительность слота), активация/деактивация, удаление
- 🛠 Услуги — добавление (название, цена, длительность), удаление
- 📆 Записи на дату — просмотр и отмена записей по конкретному дню
- 📢 Рассылка — сообщение всем зарегистрированным клиентам

Уведомления администраторам приходят автоматически при каждой новой записи.

---

## 1. Локальный запуск (для теста)

```bash
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# впишите в .env свой BOT_TOKEN и ADMIN_IDS

python -m gbot.main
```

Бот создаст файл `grooming.db` (SQLite) автоматически при первом запуске.

---

## 2. Деплой на Render

### Шаг 1 — репозиторий
Залейте эту папку в git-репозиторий (GitHub/GitLab):

```bash
git init
git add .
git commit -m "grooming bot init"
git branch -M main
git remote add origin <ваш-репозиторий>
git push -u origin main
```

### Шаг 2 — создание сервиса на Render
1. Зайдите на [render.com](https://render.com) → **New → Web Service**.
2. Подключите ваш git-репозиторий.
3. Настройки:
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python -m gbot.main`
   - **Plan**: Free
4. В разделе **Environment Variables** добавьте:
   - `BOT_TOKEN` — токен от @BotFather
   - `ADMIN_IDS` — ваш telegram id (можно несколько через запятую)
   - `DATABASE_URL` — можно оставить `sqlite+aiosqlite:///grooming.db`
   - `PYTHON_VERSION` — **обязательно поставьте `3.11.9`**. Без этой переменной Render иногда берёт самую новую версию Python (3.13/3.14), а под неё ещё нет готовых бинарных пакетов для некоторых зависимостей (например `pydantic-core`), из-за чего сборка падает с ошибкой про `maturin`/`cargo`/read-only file system.
5. Нажмите **Create Web Service** — Render соберёт и запустит бота.

Если сервис уже создан и сборка упала с ошибкой про `maturin failed` / `cargo metadata` / `Read-only file system` — зайдите в **Settings → Environment**, добавьте `PYTHON_VERSION=3.11.9` и нажмите **Manual Deploy → Clear build cache & deploy**.

Render сам передаёт свободный порт через переменную `PORT`, наш `main.py` уже её использует — ничего дополнительно настраивать не нужно.

> ⚠️ **Важно про SQLite на Render (бесплатный тариф):** файловая система на free-плане временная — при перезапуске/деплое сервиса файл `grooming.db` обнулится. Для тестового запуска это ок. Если нужно сохранять данные насовсем — подключите бесплатную PostgreSQL от Render и укажите её `DATABASE_URL` в переменных окружения (формат `postgresql+asyncpg://...`, дополнительно потребуется добавить пакет `asyncpg` в `requirements.txt`). Это можно сделать позже, когда решите, что данные важно сохранять постоянно.

### Шаг 3 — UptimeRobot (чтобы бесплатный сервис не "засыпал")
1. Зарегистрируйтесь на [uptimerobot.com](https://uptimerobot.com).
2. Создайте монитор типа **HTTP(s)**.
3. URL — адрес вашего сервиса на Render, например `https://grooming-bot.onrender.com/ping`.
4. Интервал проверки — 5 минут.

Бот отвечает на `/` и `/ping` простым текстом — этого достаточно, чтобы Render не усыплял сервис.

---

## 3. Структура проекта

```
grooming/
├── bot/
│   ├── config.py            # переменные окружения
│   ├── main.py               # точка входа: polling + веб-сервер
│   ├── database/
│   │   ├── models.py         # User, Master, Service, Booking
│   │   ├── db.py             # engine/сессии, init_db
│   │   └── requests.py       # CRUD-функции
│   ├── handlers/
│   │   ├── registration.py   # /start, регистрация
│   │   ├── client.py         # запись, "мои записи"
│   │   └── admin.py          # админ-панель
│   ├── keyboards/
│   │   ├── client_kb.py
│   │   ├── admin_kb.py
│   │   └── callbacks.py      # CallbackData фабрики
│   ├── states/states.py      # FSM-состояния
│   └── utils/slots.py        # генерация свободных слотов времени
├── requirements.txt
├── render.yaml
├── Procfile
└── .env.example
```

## 4. Как добавить мастера/услугу после деплоя

1. Напишите боту `/admin` (нужно, чтобы ваш telegram id был в `ADMIN_IDS`).
2. «👨‍🔧 Мастера» → «➕ Добавить мастера» → следуйте подсказкам (имя → рабочие дни → время начала/конца → длительность слота в минутах).
3. Аналогично для услуг через «🛠 Услуги».

После этого клиенты смогут выбирать мастера и записываться на свободное время.
