FROM python:3.13.0-slim

WORKDIR /app

# Устанавливаем зависимости ОС
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
 && rm -rf /var/lib/apt/lists/


# Копируем файлы зависимостей
COPY docker_requirements.txt .

# Устанавливаем зависимости
RUN pip install -r docker_requirements.txt

# Копируем остальные файлы проекта
COPY . .

EXPOSE 1088

# Запуск через python -m src
CMD ["python", "-m", "src"]