FROM python:3.13.0-slim

WORKDIR /app

# Устанавливаем PostgreSQL клиент
RUN apt-get update && apt-get install -y postgresql-client curl && rm -rf /var/lib/apt/lists/*

# Копируем файлы зависимостей
COPY docker_requirements.txt .

# Устанавливаем зависимости
RUN pip install -r docker_requirements.txt


# Копируем остальные файлы проекта
COPY . .

