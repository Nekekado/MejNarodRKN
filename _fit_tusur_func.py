import sqlite3
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration
import torch
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
import faiss

# Инициализация модели и процессора
device = "cuda" if torch.cuda.is_available() else "cpu"
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base").to(device)

# Подключение к базе данных
db_name = 'image_data.db'

# Функция для генерации описания изображения
def generate_caption(image_path):
    try:
        image = Image.open(image_path).convert("RGB")  # Конвертация в RGB
        inputs = processor(image, return_tensors="pt").to(device)
        out = model.generate(**inputs)
        description = processor.decode(out[0], skip_special_tokens=True)
        return description
    except Exception as e:
        print(f"Ошибка при обработке {image_path}: {e}")
        return None

# Функция для добавления нового изображения в базу данных
def add_image_to_db(image_path):
    # Генерируем описание изображения
    description = generate_caption(image_path)
    if description is None:
        print("Не удалось получить описание изображения.")
        return

    # Извлекаем имя изображения из пути
    image_name = image_path.split('/')[-1]  # Если используется Windows, для Linux замените на '/'

    # Получаем новую папку для новых данных
    source_file = "New_data"
    
    # Подключаемся к базе данных и добавляем запись
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # Вставляем новое изображение и описание в таблицу images
    cursor.execute('''INSERT INTO images (description, source_file, image_name) VALUES (?, ?, ?)''',
                   (description, source_file, image_name))
    
    conn.commit()
    conn.close()
    
    print(f"Изображение '{image_name}' успешно добавлено в базу данных с описанием: '{description}' и датой: '{source_file}'")

# Подключение к базе данных SQLite и создание таблицы при необходимости
def initialize_db(db_name='image_data.db'):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        description TEXT,
        source_file TEXT,
        image_name TEXT
    )''')
    conn.commit()
    return conn, cursor

# Функция для загрузки всех данных из базы данных
def load_data_from_db(cursor):
    cursor.execute("SELECT description, source_file, image_name FROM images")
    return cursor.fetchall()

# Функция для фильтрации данных по фразе
def filter_data_by_phrase(cursor, search_phrase):
    cursor.execute("SELECT description, source_file, image_name FROM images WHERE description LIKE ?", 
                   ('%' + search_phrase + '%',))
    return cursor.fetchall()

# Функция для создания эмбеддингов и инициализации индекса FAISS
def create_embeddings_and_index(descriptions, model):
    embeddings = model.encode(descriptions)
    embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)  # Нормализация
    d = embeddings.shape[1]
    index = faiss.IndexFlatIP(d)  # Индекс на основе скалярного произведения
    index.add(embeddings)
    return embeddings, index

# Функция для добавления похожих результатов в случае нехватки
def add_similar_results(search_phrase, model, index, descriptions, source_files, image_names, filtered_data):
    query_embedding = model.encode([search_phrase])
    query_embedding = query_embedding / np.linalg.norm(query_embedding, axis=1, keepdims=True)  # Нормализация

    k = 40 - len(filtered_data)  # Получаем количество дополнительных результатов

    if k > 0:
        distances, indices = index.search(query_embedding, k)  # Находим похожие результаты

        # Создаем список новых результатов с добавлением similarity
        additional_results = [{
            "description": descriptions[i],
            "source_file": source_files[i],
            "image_name": image_names[i],
            "similarity": distances[0][j]  # Добавляем схожесть для каждого результата
        } for j, i in enumerate(indices[0])]

        # Добавляем дополнительные результаты в список
        filtered_data.extend(additional_results)

    return filtered_data

def search_top_20_similar(search_phrase, db_name='image_data.db'):
    # Инициализация базы данных и загрузка данных
    conn, cursor = initialize_db(db_name)
    data = load_data_from_db(cursor)
    descriptions = [row[0] for row in data]
    source_files = [row[1] for row in data]
    image_names = [row[2] for row in data]

    # Инициализация модели для создания эмбеддингов
    embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    
    # Фильтрация данных по фразе
    filtered_data = filter_data_by_phrase(cursor, search_phrase)

    # Если есть отфильтрованные данные, добавляем схожесть
    if filtered_data:
        # Получаем эмбеддинг для поисковой фразы
        query_embedding = embedding_model.encode([search_phrase])
        query_embedding = query_embedding / np.linalg.norm(query_embedding, axis=1, keepdims=True)  # Нормализация

        # Рассчитываем схожесть для отфильтрованных данных
        similarities = []
        for entry in filtered_data:
            # Находим схожесть для каждого описания
            description_embedding = embedding_model.encode([entry[0]])
            description_embedding = description_embedding / np.linalg.norm(description_embedding, axis=1, keepdims=True)
            similarity = np.dot(query_embedding, description_embedding.T)  # Скалярное произведение
            similarities.append(similarity[0][0])  # Сохраняем схожесть
        
        # Добавляем схожесть в filtered_data
        for i, entry in enumerate(filtered_data):
            entry_dict = {
                "description": entry[0],
                "source_file": entry[1],
                "image_name": entry[2],
                "similarity": similarities[i]
            }
            filtered_data[i] = entry_dict

    # Инициализация индекса FAISS
    embeddings, index = create_embeddings_and_index(descriptions, embedding_model)

    # Если отфильтрованных данных меньше 20, добавляем похожие результаты
    if len(filtered_data) < 40:
        filtered_data = add_similar_results(search_phrase, embedding_model, index, descriptions, source_files, image_names, filtered_data)

    # Преобразование результатов в DataFrame
    df_results = pd.DataFrame(filtered_data)

    # Убираем дубликаты по столбцам description, source_file, image_name
    df_results = df_results.drop_duplicates(subset=['description', 'source_file', 'image_name'])

    # Сортировка и отбор топ-20 по схожести
    df_results = df_results.sort_values(by='similarity', ascending=False).head(20)

    # Закрытие соединения с базой данных
    conn.close()

    return df_results

