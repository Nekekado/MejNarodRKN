from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from _fit_tusur_func import generate_caption, search_top_20_similar  # Импортируем функции для генерации описания и поиска схожих изображений
import os

# Создаем экземпляр Flask-приложения
app = Flask(__name__)

# Устанавливаем секретный ключ для безопасности сессий и флеш-сообщений
app.secret_key = "your_secret_key"

# Указываем папку для загрузки файлов
UPLOAD_FOLDER = "uploads"
# Создаем папку для загрузок, если она не существует
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Основная функция для обработки запросов на главной странице.
    Обрабатывает GET и POST-запросы для загрузки изображений или текстового поиска.
    """
    search_text = ""  # Переменная для хранения текста поиска
    results = []  # Список для хранения результатов поиска
    uploaded_image_url = None  # Переменная для хранения пути к загруженному изображению

    # Обработка POST-запроса, если была отправлена форма
    if request.method == 'POST':
        # Получаем загруженный файл и текстовый ввод от пользователя
        file = request.files.get('file')
        search_text = request.form.get('text', '').strip()  # Убираем пробелы по краям

        if file and file.filename:  # Проверка, загружен ли файл
            # Сохраняем загруженный файл в папке UPLOAD_FOLDER
            image_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(image_path)

            # Генерируем описание загруженного изображения
            description = generate_caption(image_path)
            if description:
                # Если описание успешно сгенерировано, выводим его пользователю
                flash(f"Описание изображения: {description}", "success")
            else:
                # Если описание не удалось создать, показываем сообщение об ошибке
                flash("Не удалось создать описание изображения.", "error")

            # Ищем схожие изображения по сгенерированному описанию
            results_df = search_top_20_similar(description)
            if not results_df.empty:
                # Если найдены схожие изображения, конвертируем результат в список словарей
                results = results_df.to_dict(orient="records")
                flash(f"Результаты для изображения: {file.filename}", "info")
            else:
                # Если схожие изображения не найдены, показываем сообщение об ошибке
                flash("Не удалось найти схожие изображения.", "error")

        elif search_text:  # Проверка, введен ли текст для поиска
            # Ищем схожие изображения по текстовому запросу
            results_df = search_top_20_similar(search_text)
            if not results_df.empty:
                # Если найдены схожие изображения, конвертируем результат в список словарей
                results = results_df.to_dict(orient="records")
                flash(f"По вашему запросу: {search_text}", "info")
            else:
                # Если схожие изображения не найдены, показываем сообщение об ошибке
                flash("По вашему запросу ничего не найдено.", "error")
        else:
            # Если ни файл, ни текст не были переданы, показываем предупреждение
            flash("Пожалуйста, выберите изображение или введите текст для загрузки.", "warning")

    # Отображаем шаблон index.html, передаем в него результаты поиска, текст поиска и URL загруженного изображения
    return render_template("index.html", results=results, search_text=search_text, uploaded_image_url=uploaded_image_url)

# Запуск приложения
if __name__ == '__main__':
    # Включаем отладочный режим для упрощения отладки
    app.run(debug=True)
