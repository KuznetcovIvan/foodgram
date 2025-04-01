![Платформа для хранения рецептов](frontend/src/images/logo.png)

[![Платформа для хранения рецептов](https://img.shields.io/badge/Платформа%20для%20хранения%20рецептов-FF9900?style=for-the-badge)](http://food-gram.hopto.org)




[![Django](https://img.shields.io/badge/Django-3.2-green)](https://www.djangoproject.com/)
[![React](https://img.shields.io/badge/React-18-blue)](https://reactjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13-blue)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-20.10-blue)](https://www.docker.com/)

[![Main Foodgram workflow](https://github.com/KuznetcovIvan/foodgram/actions/workflows/main.yml/badge.svg)](https://github.com/KuznetcovIvan/foodgram/actions/workflows/main.yml)


## О проекте  
**FOODGRAM** — это веб-платформа, где пользователи могут создавать, хранить и делиться кулинарными рецептами. Проект разработан в рамках обучения и включает полный функционал для удобного ведения базы рецептов, списка покупок и избранных блюд.  

## Функциональность  
- Регистрация и аутентификация пользователей  
- Создание, редактирование и удаление рецептов  
- Загрузка изображений блюд  
- Добавление рецептов в избранное  
- Формирование списка покупок на основе выбранных рецептов  
- Просмотр рецептов других пользователей  

## Технологический стек  
- **Backend**: Python, Django, Django REST Framework  
- **База данных**: PostgreSQL (продакшен), SQLite (локально)  
- **Frontend**: React  
- **Контейнеризация**: Docker, Docker Compose  
- **CI/CD**: GitHub Actions, Docker Hub  

## Развёртывание проекта  

### 1. Клонирование репозитория  
```bash
git clone https://github.com/<ваш_логин>/foodgram.git
cd foodgram
```  

### 2. Настройка окружения  
Создайте файл `.env` в корне проекта и добавьте переменные:  
```bash
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=foodgram_password
POSTGRES_DB=foodgram
DB_HOST=db
DB_PORT=5432
SECRET_KEY=<Ваш секретный ключ>
DEBUG=False
ALLOWED_HOSTS=localhost 127.0.0.1 your-foodgram-domain.com
DB_TYPE=postgres
```  

### 3. Запуск контейнеров  
```bash
docker-compose up -d --build
```  

### 4. Выполнение миграций и создание суперпользователя  
```bash
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py createsuperuser
```  

### 5. Подключение Nginx и SSL  
Добавьте домен в конфигурацию Nginx, установите SSL через Certbot:  
```bash
sudo certbot --nginx -d your-foodgram-domain.com
```  

## Настройка CI/CD  

Добавьте секреты в GitHub (**Settings > Secrets and variables > Actions > Secrets**):  

**DockerHub:**  
- `DOCKER_USERNAME` = ваш логин  
- `DOCKER_PASSWORD` = ваш пароль  

**SSH-доступ к серверу:**  
- `HOST` = IP-адрес  
- `USER` = Имя пользователя  
- `SSH_KEY` = Приватный ключ  
- `SSH_PASSPHRASE` = Пароль к ключу  

**Telegram-уведомления:**  
- `TELEGRAM_TO` = ID чата  
- `TELEGRAM_TOKEN` = Токен бота  

### Запуск деплоя  
```bash
git add .
git commit -m "Deploy Foodgram"
git push
```  

Проект будет автоматически развёрнут и доступен по адресу **your-foodgram-domain.com**.  

 
### Автор:  [Иван Кузнецов](https://github.com/KuznetcovIvan)

