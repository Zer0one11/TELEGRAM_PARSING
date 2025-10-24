# api/search.py

# ИМПОРТЫ
from flask import request, jsonify
import random
import os
import json
import pathlib 
import re
# Заглушка, так как Serverless Function не запускается как полноценный Flask-сервер
# Мы используем его функционал для обработки запросов

# === КОНФИГУРАЦИЯ ===
# Замените на свои секретные ключи! 
VALID_API_KEYS = ["YOUR_SECRET_KEY_12345", "ANOTHER_KEY_67890"] 

# *** ПУТЬ К ФАЙЛУ БАЗЫ ДАННЫХ ДЛЯ API (usernames_base2.txt) ***
DB_FILE_NAME = 'usernames_base2.txt'

USERNAMES = []

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


# --- Функция для загрузки базы ---
def load_database():
    global USERNAMES
    if USERNAMES:
        return
    
    # Путь к текущему файлу (search.py)
    current_dir = pathlib.Path(__file__).resolve().parent 
    full_path = current_dir / DB_FILE_NAME
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            raw_lines = f.readlines()
        
        # Обработка всех собранных строк
        if raw_lines:
            USERNAMES = [line.strip() for line in raw_lines if line.strip()]
            USERNAMES = list(set(USERNAMES)) # Удаляем дубликаты
        else:
            USERNAMES = []
            
        print(f"База данных {DB_FILE_NAME} загружена. Общий итог: {len(USERNAMES)} уникальных юзеров.")

    except FileNotFoundError:
        print(f"КРИТИЧЕСКАЯ ОШИБКА: Файл базы данных {DB_FILE_NAME} не найден в папке API.")
        USERNAMES = []
    except Exception as e:
        print(f"Ошибка при чтении файла {DB_FILE_NAME}: {e}")

load_database()


def handler(event, context):
    """
    Основной обработчик Vercel Serverless Function.
    """
    
    # 1. Проверка API-ключа
    api_key = event.get('queryStringParameters', {}).get('key')
    if not api_key or api_key not in VALID_API_KEYS:
        return {
            "statusCode": 401,
            "body": json.dumps({"error": "Недействительный или отсутствующий API-ключ."}),
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
        # Если база не загрузилась, возвращаем явную ошибку JSON
         return {
            "statusCode": 500,
            "body": json.dumps({"error": "База данных API не загружена. Проверьте путь к usernames_base2.txt"}),
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
        
        found = [raw_link for raw_link in USERNAMES if query in extract_clean_username(raw_link).lower()]
        
        results = found
        message = f"Найдено {len(results)} юзеров по запросу '{query}'."
        
    else:
        # 4. Обработка ошибки
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Требуется параметр 'query' или 'random=true'."}),
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
    
