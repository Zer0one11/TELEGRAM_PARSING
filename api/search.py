# api/search.py

# Импорты
import random
import os
import json
import re 
# Flask импортируется для удовлетворения требований сборки Vercel
from flask import request, jsonify 

# === КОНФИГУРАЦИЯ API ===
VALID_API_KEYS = ["YOUR_SECRET_KEY_12345", "ANOTHER_KEY_67890"] 

# *** ПУТЬ К БАЗЕ ДАННЫХ ДЛЯ API ***
# Ищет telegram_all_users.txt в папке, где лежит этот файл (api/)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE_NAME = 'telegram_all_users.txt' 

USERNAMES = []

def extract_clean_username(linkString):
    match = re.search(r'(?:t\.me\/|@)([a-zA-Z0-9_]{5,})', linkString, re.IGNORECASE)
    if match and match.group(1):
        return match.group(1)
    return linkString.strip().replace('@', '')


# --- Функция для загрузки базы ---
def load_database():
    global USERNAMES
    if USERNAMES:
        return
    
    full_path = os.path.join(BASE_DIR, DB_FILE_NAME)
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            raw_lines = f.readlines()
        
        if raw_lines:
            USERNAMES = list(set([line.strip() for line in raw_lines if line.strip()]))
        else:
            USERNAMES = []
            
        print(f"База данных {DB_FILE_NAME} загружена. Итог: {len(USERNAMES)} юзеров.")

    except FileNotFoundError:
        # Если эта ошибка появляется в логах Vercel, значит, файл лежит не там.
        print(f"КРИТИЧЕСКАЯ ОШИБКА: Файл базы данных {DB_FILE_NAME} не найден по пути: {full_path}")
        USERNAMES = []
    except Exception as e:
        print(f"Общая ошибка при загрузке базы: {e}")

load_database()


def handler(event, context):
    """
    Основной обработчик Vercel Serverless Function, использующий Flask-подобный синтаксис.
    """
    
    # 1. Проверка API-ключа
    api_key = event.get('queryStringParameters', {}).get('key')
    if not api_key or api_key not in VALID_API_KEYS:
        return {
            "statusCode": 401,
            "body": json.dumps({"error": "Недействительный или отсутствующий API-ключ."}),
            "headers": {"Content-Type": "application/json"}
        }

    # 2. Обработка запроса
    query_params = event.get('queryStringParameters', {})
    query = query_params.get('query')
    is_random = query_params.get('random')
    count = int(query_params.get('count', 20))
    
    results = []
    message = ""
    
    if not USERNAMES:
         # Возвращаем 500 ошибку, если база не загружена
         return {
            "statusCode": 500,
            "body": json.dumps({"error": "База данных API не загружена. Проверьте, что telegram_all_users.txt находится в папке api/"}),
            "headers": {"Content-Type": "application/json"}
        }

    if is_random and is_random.lower() == 'true':
        if USERNAMES:
            results = random.sample(USERNAMES, min(count, len(USERNAMES)))
        message = f"Выведено {len(results)} случайных юзеров."
        
    elif query:
        query = query.lower().strip().replace('@', '')
        found = [raw_link for raw_link in USERNAMES if query in extract_clean_username(raw_link).lower()]
        results = found
        message = f"Найдено {len(results)} юзеров по запросу '{query}'."
        
    else:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Требуется параметр 'query' или 'random=true'."}),
            "headers": {"Content-Type": "application/json"}
        }

    # 3. Форматирование и возврат JSON
    formatted_results = [
        {"username": user, "link": f"https://t.me/{extract_clean_username(user)}"} 
        for user in results
    ]

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
    
