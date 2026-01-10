# GeniusElectro - Django REST API

Веб-приложение на Django REST Framework для управления электроникой.

## Требования

- Python 3.8+
- PostgreSQL
- Virtual Environment (venv)

## Установка и настройка

### 1. Активация виртуального окружения

Если у вас уже есть виртуальное окружение в папке `env`, активируйте его:

**Windows (PowerShell):**
```powershell
.\env\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
.\env\Scripts\activate.bat
```

**Linux/Mac:**
```bash
source env/bin/activate
```

### 2. Установка зависимостей

Установите все необходимые пакеты из файла `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 3. Настройка базы данных

Создайте файл `.env` в корне проекта со следующим содержимым:

```env
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_HOST=localhost
DB_PORT=5432
```

Замените значения на ваши реальные данные для подключения к PostgreSQL.

### 4. Применение миграций

Перед запуском сервера необходимо применить миграции базы данных:

```bash
python manage.py migrate
```

### 5. Создание суперпользователя (опционально)

Если вам нужен доступ к административной панели Django:

```bash
python manage.py createsuperuser
```

## Запуск проекта

### Запуск с помощью Uvicorn

Для запуска проекта с использованием Uvicorn выполните следующую команду:

```bash
uvicorn config.asgi:application --host 0.0.0.0 --port 8000 --reload
```

**Параметры команды:**
- `config.asgi:application` - путь к ASGI приложению
- `--host 0.0.0.0` - сервер будет доступен на всех сетевых интерфейсах
- `--port 8000` - порт для запуска сервера (можно изменить)
- `--reload` - автоматическая перезагрузка при изменении кода (для разработки)

После запуска сервер будет доступен по адресу: **http://localhost:8000**

### Альтернативный способ запуска (Django development server)

Вы также можете использовать стандартный сервер разработки Django:

```bash
python manage.py runserver
```

## API Документация

После запуска сервера доступна интерактивная документация API:

- **Swagger UI**: http://localhost:8000/docs/
- **ReDoc**: http://localhost:8000/redoc/
- **Schema JSON**: http://localhost:8000/schema/

## Административная панель

Административная панель Django доступна по адресу:

- http://localhost:8000/admin/

## Структура проекта

```
GeniusElectro/
├── apps/              # Приложения проекта
│   └── v1/           # API версия 1
├── config/           # Конфигурация проекта
│   ├── asgi.py       # ASGI конфигурация
│   ├── settings.py   # Настройки Django
│   ├── urls.py       # URL маршруты
│   └── wsgi.py       # WSGI конфигурация
├── env/              # Виртуальное окружение
├── manage.py         # Django management скрипт
└── requirements.txt  # Зависимости проекта
```

## Основные технологии

- **Django 6.0** - веб-фреймворк
- **Django REST Framework** - для создания REST API
- **Uvicorn** - ASGI сервер
- **PostgreSQL** - база данных
- **JWT Authentication** - аутентификация через JWT токены
- **drf-spectacular** - генерация OpenAPI документации
- **CORS Headers** - поддержка CORS

## Полезные команды

### Создание миграций
```bash
python manage.py makemigrations
```

### Применение миграций
```bash
python manage.py migrate
```

### Создание суперпользователя
```bash
python manage.py createsuperuser
```

### Сбор статических файлов
```bash
python manage.py collectstatic
```

### Запуск Python shell с Django
```bash
python manage.py shell
```

## Генерация тестовых данных

Проект включает команды для генерации тестовых данных для различных приложений.

### Генерация данных для Products (Товары)

Создает тестовые данные для категорий, подкатегорий и товаров:

```bash
python manage.py populate_fake_data
```

Эта команда создает:
- Главные категории (MainCategory) с изображениями
- Подкатегории (SubCategory) с изображениями
- Товары (Product) с различными характеристиками
- Изображения товаров (ProductImage)
- Метраж товаров (ProductMeterage)
- Избранные товары (Favourite)

**Примечание:** Команда автоматически удаляет все существующие данные перед созданием новых.

### Генерация данных для Sites (Контакты и Партнеры)

Создает тестовые данные для контактной информации и партнеров:

```bash
# Создать 5 партнеров (по умолчанию)
python manage.py populate_sites_data --partners 5

# Создать 10 партнеров
python manage.py populate_sites_data --partners 10

# Удалить существующие данные и создать новые
python manage.py populate_sites_data --clear --partners 8
```

**Параметры:**
- `--partners N` - количество создаваемых партнеров (по умолчанию: 5)
- `--clear` - удалить существующие данные перед созданием новых

**Что создается:**
- Контактная информация (Contact) - создается только один раз, если еще не существует
- Партнеры (Partner) с изображениями

### Генерация данных для Orders (Заказы)

Создает тестовые данные для заказов:

```bash
python manage.py populate_order_data
```

**Примечание:** Проверьте наличие этой команды в проекте.

## Разработка

При разработке рекомендуется использовать флаг `--reload` для автоматической перезагрузки сервера при изменении кода.

Для продакшн окружения рекомендуется использовать:
- Gunicorn с Uvicorn workers
- Nginx как reverse proxy
- Настроить правильные настройки безопасности в `settings.py`

## Примечания

- Убедитесь, что PostgreSQL запущен и доступен
- Проверьте, что все переменные окружения в `.env` файле настроены правильно
- Для продакшн окружения измените `DEBUG = False` в `settings.py`
- Настройте `ALLOWED_HOSTS` для вашего домена

## Поддержка

При возникновении проблем проверьте:
1. Активировано ли виртуальное окружение
2. Установлены ли все зависимости
3. Настроена ли база данных
4. Применены ли миграции

