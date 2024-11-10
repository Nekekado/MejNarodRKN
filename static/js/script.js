// Получение элементов интерфейса
const generateCaptionButton = document.getElementById('generateCaptionButton'); // Кнопка для генерации описания изображения
const searchSimilarButton = document.getElementById('searchSimilarButton'); // Кнопка для поиска схожих изображений
const downloadZipButton = document.getElementById('downloadZip'); // Кнопка для скачивания ZIP-файла с изображениями
const resultMessage = document.getElementById('resultMessage'); // Блок для отображения сообщений о результате
const uploadForm = document.getElementById('uploadForm'); // Форма для загрузки изображений
const loader = document.getElementById('loader'); // Элемент индикатора загрузки (кружок)
const imageFrames = document.querySelector('.results'); // Контейнер для показа результатов (найденных изображений)

// Получаем элементы для выбора файла и предварительного просмотра изображения
const fileInput = document.querySelector('input[type="file"]'); // Инпут для выбора файла
const imagePreview = document.getElementById('imagePreview'); // Блок для предварительного просмотра изображения
const uploadedImage = document.getElementById('uploadedImage'); // Элемент img для отображения загруженного изображения

// Массив для хранения путей к изображениями из результатов поиска
let imagePaths = [];

// Событие, отслеживающее изменение файла в input
fileInput.addEventListener('change', function() {
    const file = fileInput.files[0]; // Получаем выбранный файл

    if (file) {
        // Показываем блок предварительного просмотра
        imagePreview.style.display = 'block';

        // Создаем URL для файла и задаем его в качестве источника для изображения
        const fileURL = URL.createObjectURL(file);
        uploadedImage.src = fileURL;
    } else {
        // Если файл не выбран, скрываем блок предварительного просмотра
        imagePreview.style.display = 'none';
    }
});

// Событие отправки формы для загрузки изображения
uploadForm.addEventListener('submit', function (e) {
    loader.style.display = 'block'; // Показываем индикатор загрузки
    imageFrames.style.opacity = '0.5'; // Затемняем контейнер с результатами для визуального эффекта
});

// Событие для кнопки "Сгенерировать описание"
generateCaptionButton.addEventListener('click', function() {
    const fileInput = document.getElementById('fileInput'); // Поле выбора файла
    const formData = new FormData(); // Создаем объект FormData для отправки данных на сервер
    formData.append('file', fileInput.files[0]); // Добавляем файл в FormData

    // Запрос к серверу для генерации описания
    fetch('/generate_caption', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json()) // Преобразуем ответ в JSON
    .then(data => {
        if (data.description && data.results) {
            // Отображаем описание и результаты поиска
            resultMessage.innerText = `Описание: ${data.description}`;
            displayImages(data.results); // Функция для отображения найденных изображений
            imagePaths = data.results.map(result => result.image_path); // Сохраняем пути к найденным изображениям
            downloadZipButton.style.display = 'inline-block'; // Показываем кнопку для скачивания ZIP-файла
        } else {
            // Если произошла ошибка, выводим сообщение
            resultMessage.innerText = 'Ошибка: ' + data.error;
        }
    })
    .catch(error => resultMessage.innerText = 'Произошла ошибка при загрузке изображения.'); // Сообщение об ошибке при сбое запроса
});

// Событие для кнопки "Поиск схожих изображений"
searchSimilarButton.addEventListener('click', function() {
    const searchInput = document.getElementById('searchInput').value; // Получаем текстовый запрос пользователя
    const formData = new FormData();
    formData.append('search_phrase', searchInput); // Добавляем запрос в FormData

    // Запрос к серверу для поиска схожих изображений
    fetch('/search_similar', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.results) {
            displayImages(data.results); // Отображаем найденные изображения
            imagePaths = data.results.map(result => result.image_path); // Сохраняем пути к найденным изображениям
            downloadZipButton.style.display = 'inline-block'; // Показываем кнопку для скачивания ZIP-файла
        } else {
            resultMessage.innerText = 'Ошибка: ' + data.error; // Сообщение об ошибке
        }
    })
    .catch(error => resultMessage.innerText = 'Произошла ошибка при поиске.'); // Сообщение об ошибке при сбое запроса
});

// Событие для кнопки "Скачать ZIP" с найденными изображениями
downloadZipButton.addEventListener('click', function() {
    fetch('/download_zip', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ image_paths: imagePaths }) // Передаем пути к изображениям в теле запроса
    })
    .then(response => response.blob()) // Получаем ZIP-файл как Blob
    .then(blob => {
        const link = document.createElement('a'); // Создаем временную ссылку для скачивания файла
        link.href = URL.createObjectURL(blob);
        link.download = 'images.zip'; // Задаем имя загружаемого файла
        link.click(); // Инициируем скачивание
    })
    .catch(error => resultMessage.innerText = 'Произошла ошибка при скачивании ZIP.'); // Сообщение об ошибке при сбое загрузки
});

// Функция для отображения найденных изображений
function displayImages(images) {
    // Скрываем индикатор загрузки и снимаем затенение с контейнера с результатами
    loader.style.display = 'none';
    imageFrames.style.opacity = '1';

    imageFrames.innerHTML = ''; // Очищаем контейнер с предыдущими результатами
    images.forEach(image => {
        const frame = document.createElement('div'); // Создаем div для каждого изображения
        frame.classList.add('photo-frame'); // Добавляем CSS-класс для стиля

        const img = document.createElement('img'); // Создаем элемент img для изображения
        img.src = image.image_path; // Устанавливаем путь к изображению
        img.alt = image.description; // Устанавливаем описание как атрибут alt
        img.classList.add('frame-image'); // Добавляем CSS-класс для стиля

        const descriptionDiv = document.createElement('div'); // Блок для описания изображения
        descriptionDiv.classList.add('description'); // Добавляем CSS-класс

        const descriptionText = document.createElement('p'); // Параграф для текста описания
        descriptionText.innerHTML = `<strong>Описание:</strong> ${image.description}`;

        descriptionDiv.appendChild(descriptionText); // Добавляем описание в div
        frame.appendChild(img); // Добавляем изображение в div
        frame.appendChild(descriptionDiv); // Добавляем описание в div
        imageFrames.appendChild(frame); // Добавляем фрейм изображения в контейнер результатов
    });
}
