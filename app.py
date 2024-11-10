from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from _fit_tusur_func import generate_caption, search_top_20_similar  # Импорт функций
import os

app = Flask(__name__)
app.secret_key = "your_secret_key"

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    search_text = ""
    results = []  # Список для хранения результатов
    if request.method == 'POST':
        # Проверка, загружено ли изображение или введен текст
        file = request.files.get('file')
        search_text = request.form.get('text', '').strip()

        if file and file.filename:  # Если загружен файл изображения
            image_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(image_path)

            # Генерация описания для загруженного изображения
            description = generate_caption(image_path)
            if description:
                flash(f"Описание изображения: {description}", "success")
            else:
                flash("Не удалось создать описание изображения.", "error")

            # Поиск схожих изображений
            results_df = search_top_20_similar(description)  # Получаем схожие изображения
            if not results_df.empty:
                # Преобразуем результаты в список для отображения
                results = results_df.to_dict(orient="records")
                flash(f"Результаты для изображения: {file.filename}", "info")
            else:
                flash("Не удалось найти схожие изображения.", "error")

        elif search_text:  # Если введен текст для поиска
            results_df = search_top_20_similar(search_text)
            if not results_df.empty:
                # Преобразуем результаты в список для отображения
                results = results_df.to_dict(orient="records")
                flash(f"По вашему запросу: {search_text}", "info")
            else:
                flash("По вашему запросу ничего не найдено.", "error")
        else:
            flash("Пожалуйста, выберите изображение или введите текст для загрузки.", "warning")

    return render_template("index.html", results=results, search_text=search_text)

if __name__ == '__main__':
    app.run(debug=True)
