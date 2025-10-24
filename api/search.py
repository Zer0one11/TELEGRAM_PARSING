# api/search.py

from flask import Flask, request, jsonify
import random
import os

# Flask требует, чтобы его импортировали, но Vercel Serverless Functions
# используют его по-своему, не запуская напрямую.
# Мы определяем простую функцию-обработчик.

# === КОНФИГУРАЦИЯ ===
# Замените на свои секретные ключи! В идеале, ключи нужно хранить в переменных среды Vercel.
VALID_API_KEYS = ["YOUR_SECRET_KEY_12345", "ANOTHER_KEY_67890"] 
DB_FILE_PATH = 'telegram_all_users.txt'
USERNAMES = []

# --- Загрузка базы данных при первом запуске функции ---
def load_database():
    global USERNAMES
    # Vercel Serverless Function выполняет код один раз и кеширует
    if USERNAMES:
        return

    # Определяем путь к файлу в Serverless среде
    full_path = os.path.join(os.getcwd(), DB_FILE_PATH)
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            raw_lines = f.readlines()
            USERNAMES = [line.strip() for line in raw_lines if line.strip()]
            USERNAMES = list(set(USERNAMES)) # Удаляем дубликаты
        # print(f"База данных загружена. Всего юзеров: {len(USERNAMES)}")
    except FileNotFoundError:
        print(f"Ошибка: Файл базы данных {DB_FILE_PATH} не найден!")

load_database()


def handler(event, context):
    """
    Основной обработчик Vercel Serverless Function.
    Это имитация Flask, адаптированная для Vercel.
    """
    
    # Мы не можем использовать стандартный request/jsonify Flask напрямую в Vercel,
    # поэтому нужно парсить данные из 'event'
    
    # 1. Проверка API-ключа
    api_key = event.get('queryStringParameters', {}).get('key')
    if not api_key or api_key not in VALID_API_KEYS:
        return {
            "statusCode": 401,
            "body": "{\"error\": \"Недействительный или отсутствующий API-ключ.\"}",
            "headers": {"Content-Type": "application/json"}
        }

    # Парсинг параметров
    query = event.get('queryStringParameters', {}).get('query')
    is_random = event.get('queryStringParameters', {}).get('random')
    count = int(event.get('queryStringParameters', {}).get('count', 20))
    
    results = []
    message = ""
    
    if is_random and is_random.lower() == 'true':
        # 2. Рандомный поиск
        if USERNAMES:
            results = random.sample(USERNAMES, min(count, len(USERNAMES)))
        message = f"Выведено {len(results)} случайных юзеров."
        
    elif query:
        # 3. Поиск по запросу
        query = query.lower().strip().replace('@', '')
        
        found = [user for user in USERNAMES if query in user.lower().replace('@', '')]
        
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
    def extract_clean_username(linkString):
        match = linkString.match(/(?:t\.me\/|@)([a-zA-Z0-9_]{5,})/i)
        return match[1] if match and match[1] else linkString.trim().replace(/^@/, '')

    formatted_results = [
        {
            "username": user, 
            # Используем extract_clean_username для гарантии чистой ссылки
            "link": f"https://t.me/{extract_clean_username(user).replace('@', '')}"
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
  
