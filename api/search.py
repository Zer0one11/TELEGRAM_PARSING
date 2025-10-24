# api/search.py

# ИМПОРТЫ
from flask import Flask, request, jsonify
import random
import os
import json
import pathlib # <- Добавлен для надежной работы с путями
import re

# === КОНФИГУРАЦИЯ ===
# Замените на свои секретные ключи! 
VALID_API_KEYS = ["lolkek", "ANOTHER_KEY_67890"] 

# Надежное определение пути к файлу базы данных относительно корня проекта
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
DB_FILE_PATH = BASE_DIR / 'telegram_all_users.txt'

USERNAMES = []

# --- Загрузка базы данных при первом запуске функции ---
def load_database():
    global USERNAMES
    if USERNAMES:
        return
    
    # Используем готовый абсолютный путь
    full_path = DB_FILE_PATH 
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            raw_lines = f.readlines()
            USERNAMES = [line.strip() for line in raw_lines if line.strip()]
            USERNAMES = list(set(USERNAMES)) # Удаляем дубликаты
        print(f"База данных загружена. Всего юзеров: {len(USERNAMES)}")
    except FileNotFoundError:
        print(f"Ошибка: Файл базы данных {DB_FILE_PATH} не найден!")
        
load_database()

def extract_clean_username(linkString):
    """
    Извлекает чистый юзернейм из любой 'грязной' строки.
    """
    # Регулярное выражение для поиска имени пользователя Telegram (минимум 5 символов)
    match = re.search(r'(?:t\.me\/|@)([a-zA-Z0-9_]{5,})', linkString, re.IGNORECASE)

    if match and match.group(1):
        return match.group(1)
    
    # Если ссылка не найдена, просто чистим строку от @ и пробелов
    return linkString.strip().replace('@', '')


def handler(event, context):
    """
    Основной обработчик Vercel Serverless Function.
    """
    
    # 1. Проверка API-ключа
    api_key = event.get('queryStringParameters', {}).get('key')
    if not api_key or api_key not in VALID_API_KEYS:
        return {
            "statusCode": 401,
            "body": "{\"error\": \"Недействительный или отсутствующий API-ключ.\"}",
            "headers": {"Content-Type": "application/json"}
        }

    # Парсинг параметров
    query_params = event.get('queryStringParameters', {})
    query = query_params.get('query')
    is_random = query_params.get('random')
    count = int(query_params.get('count', 20))
    
    results = []
    message = ""
    
    if not USERNAMES:
        # Если база не загрузилась (например, из-за ошибки пути)
         return {
            "statusCode": 500,
            "body": "{\"error\": \"База данных не загружена. Проверьте логи Vercel на предмет ошибок FileNotFoundError.\"}",
            "headers": {"Content-Type": "application/json"}
        }

    if is_random and is_random.lower() == 'true':
        # 2. Рандомный поиск
        if USERNAMES:
            results = random.sample(USERNAMES, min(count, len(USERNAMES)))
        message = f"Выведено {len(results)} случайных юзеров."
        
    elif query:
        # 3. Поиск по запросу
        query = query.lower().strip().replace('@', '')
        
        # Фильтруем по чистой версии имени пользователя
        found = [raw_link for raw_link in USERNAMES if query in extract_clean_username(raw_link).lower()]
        
        results = found
        message = f"Найдено {len(results)} юзеров по запросу '{query}'."
        
    else:
        # 4. Обработка ошибки
        return {
            "statusCode": 400,
            "body": "{\"error\": \"Требуется параметр 'query' или 'random=true'.\"}",
            "headers": {"Content-Type": "application/json"}
        }

    # 5. Форматируем результат
    formatted_results = [
        {
            "username": user, 
            "link": f"https://t.me/{extract_clean_username(user)}"
        } 
        for user in results
    ]

    # 6. Возвращаем JSON
    response_body = {
        "status": "success",
        "message": message,
        "total_results": len(formatted_results),
        "data": formatted_results
    }
    
    return {
        "statusCode": 200,
        "body": json.dumps(response_body),
        "headers": {"Content-Type": "application/json"}
    }
    
