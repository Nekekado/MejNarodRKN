const generateCaptionButton = document.getElementById('generateCaptionButton');
const searchSimilarButton = document.getElementById('searchSimilarButton');
const downloadZipButton = document.getElementById('downloadZip');
const resultMessage = document.getElementById('resultMessage');
const uploadForm = document.getElementById('uploadForm');
const loader = document.getElementById('loader');
const imageFrames = document.querySelector('.results');
// Получаем элемент выбора файла и блок для предварительного просмотра
const fileInput = document.querySelector('input[type="file"]');
const imagePreview = document.getElementById('imagePreview');
const uploadedImage = document.getElementById('uploadedImage');

let imagePaths = [];

// Отслеживаем изменение выбранного файла
fileInput.addEventListener('change', function() {
    const file = fileInput.files[0];

    if (file) {
        // Отображаем блок предварительного просмотра
        imagePreview.style.display = 'block';

        // Создаем URL для выбранного файла и устанавливаем его как источник изображения
        const fileURL = URL.createObjectURL(file);
        uploadedImage.src = fileURL;
    } else {
        // Скрываем блок предварительного просмотра, если файл не выбран
        //imagePreview.style.display = 'none';
    }
});

// Перехватываем отправку формы
uploadForm.addEventListener('submit', function (e) {
    loader.style.display = 'block'; // Показать кружок загрузки
    imageFrames.style.opacity = '0.5'; // Затенить контейнер с результатами
});

generateCaptionButton.addEventListener('click', function() {
    const fileInput = document.getElementById('fileInput');
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    fetch('/generate_caption', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.description && data.results) {
            resultMessage.innerText = `Описание: ${data.description}`;
            displayImages(data.results);
            imagePaths = data.results.map(result => result.image_path);
            downloadZipButton.style.display = 'inline-block';
        } else {
            resultMessage.innerText = 'Ошибка: ' + data.error;
        }
    })
    .catch(error => resultMessage.innerText = 'Произошла ошибка при загрузке изображения.');
});

searchSimilarButton.addEventListener('click', function() {
    const searchInput = document.getElementById('searchInput').value;
    const formData = new FormData();
    formData.append('search_phrase', searchInput);

    fetch('/search_similar', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.results) {
            displayImages(data.results);
            imagePaths = data.results.map(result => result.image_path);
            downloadZipButton.style.display = 'inline-block';
        } else {
            resultMessage.innerText = 'Ошибка: ' + data.error;
        }
    })
    .catch(error => resultMessage.innerText = 'Произошла ошибка при поиске.');
});

downloadZipButton.addEventListener('click', function() {
    fetch('/download_zip', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ image_paths: imagePaths })
    })
    .then(response => response.blob())
    .then(blob => {
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = 'images.zip';
        link.click();
    })
    .catch(error => resultMessage.innerText = 'Произошла ошибка при скачивании ZIP.');
});

function displayImages(images) {
    // Скрываем кружок загрузки и снимаем затенение, как только загрузка завершена
    loader.style.display = 'none';
    imageFrames.style.opacity = '1';


    imageFrames.innerHTML = ''; // Очистить фреймы
    images.forEach(image => {
        const frame = document.createElement('div');
        frame.classList.add('photo-frame');

        const img = document.createElement('img');
        img.src = image.image_path;
        img.alt = image.description;
        img.classList.add('frame-image');

        const descriptionDiv = document.createElement('div');
        descriptionDiv.classList.add('description');

        const descriptionText = document.createElement('p');
        descriptionText.innerHTML = `<strong>Описание:</strong> ${image.description}`;

        descriptionDiv.appendChild(descriptionText);
        frame.appendChild(img);
        frame.appendChild(descriptionDiv);
        imageFrames.appendChild(frame);
    });


}
