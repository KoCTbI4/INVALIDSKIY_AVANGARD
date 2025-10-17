const uploadInput = document.getElementById('imageUpload');
const preview = document.getElementById('preview');
const chat = document.getElementById('chat');

uploadInput.addEventListener('change', async (e) => {
  const file = e.target.files[0];
  if (!file) return;

  // Очищаем чат перед новым описанием
  chat.innerHTML = '';

  // Показываем превью
  const img = document.createElement('img');
  img.src = URL.createObjectURL(file);
  img.classList.add('img_preview'); // ← добавлен класс для стилизации
  preview.innerHTML = ''; // очищаем предыдущее изображение
  preview.appendChild(img);

  // Отправляем изображение на бэкенд (изменил имя поля на 'image')
  const formData = new FormData();
  formData.append('file', file); // ← важно: имя должно быть 'image', как в бэкенде

  // Показываем сообщение "Обработка..."
  addMessageToChat('bot', 'Обработка...');

  try {
    const response = await fetch('https://noncontinuably-meatier-ardella.ngrok-free.dev/api/describe', {
      method: 'POST',
      body: formData,
    });

    console.log("Статус ответа:", response.status);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    // Проверяем, что ответ — JSON
    const contentType = response.headers.get("content-type");
    if (!contentType || !contentType.includes("application/json")) {
      throw new Error("Ответ не является JSON");
    }

    const data = await response.json();
    console.log("Полученные данные:", data);

    // Проверяем, есть ли поле description
    if (!data || typeof data.description !== 'string') {
      throw new Error("Ответ не содержит поля 'description' или оно некорректно");
    }

    const description = data.description;

    // Удаляем сообщение "Обработка..." и добавляем новое
    chat.innerHTML = ''; // Очищаем "Обработка..."
    addMessageToChat('bot', description);

    // Озвучиваем результат (если поддерживается)
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(description);
      speechSynthesis.speak(utterance);
    }
  } catch (error) {
    console.error('Ошибка в обработке ответа:', error);
    chat.innerHTML = ''; // Очищаем "Обработка..."
    addMessageToChat('bot', 'Произошла ошибка при обработке изображения.');
  }
});

function addMessageToChat(sender, text) {
  const messageDiv = document.createElement('div');
  messageDiv.classList.add('message', sender);
  messageDiv.textContent = text;
  chat.appendChild(messageDiv);
  chat.scrollTop = chat.scrollHeight;
}

