# Metal Products Backend

Backend для сайта продажи металлопродукции с системой авторизации и ролями пользователей.

## Функциональность

- **Пользователи**: Регистрация, вход, управление профилем
- **Роли**: Администратор и Клиент
- **Авторизация**: JWT токены
- **Продукты**: Управление товарами (существующая функциональность)

## Установка и настройка

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```env
SECRET_KEY=your-secret-key-here
SERVER_HOST=http://localhost:8000
POSTGRES_URL=postgresql+asyncpg://username:password@localhost/dbname
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 3. Настройка базы данных

```bash
# Создание миграций
alembic revision --autogenerate -m "Add users table"

# Применение миграций
alembic upgrade head
```

### 4. Создание первого администратора

```bash
python create_admin.py
```

## API Endpoints

### Аутентификация

- `POST /users/register` - Регистрация нового пользователя
- `POST /users/login` - Вход пользователя
- `GET /users/me` - Получение информации о текущем пользователе

### Управление пользователями (только для админов)

- `GET /users/` - Получение списка всех пользователей
- `GET /users/{user_id}` - Получение пользователя по ID
- `PUT /users/{user_id}` - Обновление пользователя
- `DELETE /users/{user_id}` - Удаление пользователя

### Продукты

- Существующие эндпоинты для работы с продуктами

## Использование

### Запуск сервера

```bash
uvicorn app.main:app --reload
```

### Регистрация пользователя

```bash
curl -X POST "http://localhost:8000/users/register" \
     -H "Content-Type: application/json" \
     -d '{
       "email": "user@example.com",
       "username": "user123",
       "password": "password123"
     }'
```

### Вход пользователя

```bash
curl -X POST "http://localhost:8000/users/login" \
     -H "Content-Type: application/json" \
     -d '{
       "email": "user@example.com",
       "password": "password123"
     }'
```

### Использование защищенных эндпоинтов

```bash
curl -X GET "http://localhost:8000/users/me" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Роли пользователей

### Клиент (client)

- Может регистрироваться и входить в систему
- Может просматривать свой профиль
- Доступ к основным функциям сайта

### Администратор (admin)

- Все права клиента
- Может управлять всеми пользователями
- Может создавать, редактировать и удалять пользователей
- Доступ к административным функциям

## Безопасность

- Пароли хешируются с использованием bcrypt
- JWT токены для аутентификации
- Проверка ролей для доступа к административным функциям
- Валидация данных с помощью Pydantic
