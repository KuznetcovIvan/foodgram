![Платформа для хранения рецептов](frontend/src/images/logo.png)

[![Платформа для хранения рецептов](https://img.shields.io/badge/Платформа%20для%20хранения%20рецептов-FF9900?style=for-the-badge)](http://food-gram.hopto.org)

[![Django](https://img.shields.io/badge/Django-3.2-green)](https://www.djangoproject.com/)
[![React](https://img.shields.io/badge/React-18-blue)](https://reactjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13-blue)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-20.10-blue)](https://www.docker.com/)

[![Main Foodgram workflow](https://github.com/KuznetcovIvan/foodgram/actions/workflows/main.yml/badge.svg)](https://github.com/KuznetcovIvan/foodgram/actions/workflows/main.yml)

---

## О проекте
**FOODGRAM** — это веб-платформа, где пользователи могут создавать, хранить и делиться кулинарными рецептами. Проект разработан в рамках обучения и включает полный функционал для удобного ведения базы рецептов, списка покупок и избранных блюд.

---

## Функциональность

### Для всех пользователей
- Просмотр главной страницы с рецептами
- Просмотр отдельных страниц рецептов
- Просмотр профилей пользователей
- Фильтрация рецептов по тегам
- Постраничная навигация (пагинация)

### Для авторизованных пользователей
#### Работа с рецептами
- Создание собственных рецептов
- Редактирование и удаление своих рецептов
- Добавление рецептов в избранное
- Добавление рецептов в список покупок

#### Подписки
- Подписка на авторов
- Просмотр страницы "Мои подписки"
- Отписка от авторов

#### Список покупок
- Добавление/удаление рецептов в список покупок
- Скачивание списка необходимых ингредиентов в текстовом формате
- Автоматическое суммирование одинаковых ингредиентов в списке

#### Личный кабинет
- Изменение пароля
- Изменение/удаление изображения профиля
- Выход из системы

### Для администраторов
- Управление всеми моделями через админ-панель
- Поиск пользователей по имени и email
- Поиск рецептов по названию и автору
- Фильтрация рецептов по тегам
- Просмотр статистики добавления рецептов в избранное
- Поиск ингредиентов по названию

---

## Технологический стек
- **Backend**: Python, Django, Django REST Framework  
- **База данных**: PostgreSQL (продакшен), SQLite (локально)  
- **Frontend**: React  
- **Контейнеризация**: Docker, Docker Compose  
- **CI/CD**: GitHub Actions, Docker Hub  

---

## Развёртывание проекта локально

### Предварительные требования
Перед началом работы убедитесь, что у вас установлен **Git** для клонирования репозитория.

### Шаг 1: Установка Docker
#### Windows
1. Скачайте **Docker Desktop** для Windows с [официального сайта](https://www.docker.com/products/docker-desktop).
2. Запустите установщик и следуйте инструкциям мастера установки.
3. После установки запустите **Docker Desktop**.
4. Убедитесь, что **WSL 2** (Windows Subsystem for Linux) активирован на вашем компьютере.

#### macOS
1. Скачайте **Docker Desktop** для Mac с [официального сайта](https://www.docker.com/products/docker-desktop).
2. Перетащите приложение **Docker** в папку *Applications*.
3. Запустите **Docker Desktop** из папки *Applications*.

#### Linux
```bash
# Обновление пакетов
sudo apt-get update
# Установка необходимых зависимостей
sudo apt-get install apt-transport-https ca-certificates curl software-properties-common
# Добавление GPG-ключа Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
# Добавление репозитория Docker
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
# Установка Docker
sudo apt-get update && sudo apt-get install docker-ce docker-compose
# Добавление пользователя в группу docker
sudo usermod -aG docker $USER
# Применение изменений группы без перезагрузки
newgrp docker
```

### Шаг 2: Клонирование репозитория
```bash
# Клонирование репозитория
git clone https://github.com/kuznetcovivan/foodgramm.git

# Переход в директорию проекта
cd foodgramm
```

### Шаг 3: Настройка переменных окружения
Создайте файл `.env` в корне проекта со следующим содержимым:
```
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=foodgram_password
POSTGRES_DB=foodgram
DB_HOST=db
DB_PORT=5432
SECRET_KEY=  # Input-your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=localhost 127.0.0.1  # Input-your-domain-name-here
DB_TYPE=postgres
```
Примечание: Если файл .env не создан, проект запустится в режиме отладки (DEBUG=True) с использованием SQLite вместо PostgreSQL.

### Шаг 4: Запуск приложения
```bash
# Запуск контейнеров
docker-compose -f docker-compose.production.yml up -d
# Выполнение миграций
docker-compose -f docker-compose.production.yml exec backend python manage.py migrate
# Сбор статических файлов
docker-compose -f docker-compose.production.yml exec backend python manage.py collectstatic
# Копирование статических файлов в volume
sudo docker compose -f docker-compose.production.yml exec backend cp -r /app/collected_static/. /backend_static/static/
# Создание суперпользователя 
docker-compose -f docker-compose.production.yml exec backend python manage.py createsuperuser
```
### Шаг 5: Доступ к приложению
- **Веб-интерфейс**: [http://localhost:9090](http://localhost:9090)
- **Панель администратора**: [http://localhost:9090/admin/](http://localhost:9090/admin/)

### Шаг 6: Управление контейнерами
```bash
# Остановка контейнеров
docker-compose -f docker-compose.production.yml down
# Перезапуск контейнеров
docker-compose -f docker-compose.production.yml restart
# Просмотр логов
docker-compose -f docker-compose.production.yml logs -f
```
---
### Если порт 9090 уже занят
Измените порт в файле `docker-compose.production.yml`:
```yaml
gateway:
  ports:
    - 8080:80  # или любой другой свободный порт
```
---
### Автор: [Иван Кузнецов](https://github.com/KuznetcovIvan)
