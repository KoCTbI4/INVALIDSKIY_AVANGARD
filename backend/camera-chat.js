let currentImageFile = null;
let currentSessionId = null; // Не сбрасываем при загрузке изображения, если сессия уже есть

const chat = document.getElementById('chat');
const messageInput = document.getElementById('messageInput');

// Функция отправки сообщения
function sendMessage() {
  const message = messageInput.value.trim();
  if (!message && !currentImageFile) return;

  // Если есть изображение — отправляем его как сообщение пользователя
  if (currentImageFile) {
    addImageToChat(currentImageFile);
  }

  if (message) {
    // Добавляем текстовое сообщение пользователя в чат
    addMessageToChat('user', message);
    messageInput.value = '';
  }

  // Если сессия не создана — создаём её
  if (!currentSessionId) {
    if (!currentImageFile) {
      addMessageToChat('bot', 'Пожалуйста, сначала загрузите изображение.');
      return;
    }
    startSession();
    return;
  }

  // Если сессия уже есть — отправляем только вопрос
  const formData = new FormData();
  formData.append('session_id', currentSessionId);
  formData.append('question', message);

  fetch('https://noncontinuably-meatier-ardella.ngrok-free.dev/api/ask', {
    method: 'POST',
    body: formData,
  })
    .then(response => response.json())
    .then(data => {
      if (data.error) {
        addMessageToChat('bot', data.error);
      } else {
        addMessageToChat('bot', data.answer);
      }
      // Только после успешной отправки — очищаем изображение, если оно было отправлено
      if (currentImageFile) {
        currentImageFile = null;
        document.getElementById('imagePreview').style.display = 'none';
        document.getElementById('imagePreview').innerHTML = '';
      }
    })
    .catch(error => {
      console.error('Ошибка:', error);
      addMessageToChat('bot', 'Ошибка при отправке вопроса.');
    });
}

// Функция начала сессии (отправка изображения и получение session_id)
function startSession() {
  const formData = new FormData();
  formData.append('image', currentImageFile);

  fetch('https://noncontinuably-meatier-ardella.ngrok-free.dev/api/start_chat', {
    method: 'POST',
    body: formData,
  })
    .then(response => response.json())
    .then(data => {
      if (data.error) {
        addMessageToChat('bot', data.error);
      } else {
        currentSessionId = data.session_id;
        addMessageToChat('bot', data.description);
        addMessageToChat('bot', 'Теперь вы можете задавать вопросы.');
        // После успешного старта сессии — можно очистить изображение
        currentImageFile = null;
        document.getElementById('imagePreview').style.display = 'none';
        document.getElementById('imagePreview').innerHTML = '';
      }
    })
    .catch(error => {
      console.error('Ошибка при создании сессии:', error);
      addMessageToChat('bot', 'Ошибка при загрузке изображения.');
    });
}

// Добавление текстового сообщения в чат
function addMessageToChat(sender, text) {
  const messageDiv = document.createElement('div');
  messageDiv.classList.add('message', sender);
  messageDiv.textContent = text;
  chat.appendChild(messageDiv);
  chat.scrollTop = chat.scrollHeight;
}

// Добавление изображения как сообщения в чат
function addImageToChat(file) {
  const messageDiv = document.createElement('div');
  messageDiv.classList.add('message', 'user');

  const img = document.createElement('img');
  img.src = URL.createObjectURL(file);
  img.classList.add('img_preview');
  img.style.maxWidth = '100%';
  img.style.borderRadius = '8px';

  messageDiv.appendChild(img);
  chat.appendChild(messageDiv);
  chat.scrollTop = chat.scrollHeight;
}

// Обработчик загрузки изображения
document.getElementById('imageUpload').addEventListener('change', (e) => {
  const file = e.target.files[0];
  if (!file) return;

  // Не сбрасываем сессию, если она уже есть
  
  currentSessionId = null; // Это было неправильно
  

  // Показываем мини-превью рядом с полем ввода
  const previewContainer = document.getElementById('imagePreview');
  const img = document.createElement('img');
  img.src = URL.createObjectURL(file);
  img.classList.add('img_preview');

  // Очищаем контейнер
  previewContainer.innerHTML = '';

  // Создаём кнопку удаления
  const removeBtn = document.createElement('div');
  removeBtn.className = 'remove-btn';
  removeBtn.textContent = '×';
  removeBtn.onclick = function() {
    currentImageFile = null;
    previewContainer.style.display = 'none';
    previewContainer.innerHTML = '';
    addMessageToChat('bot', 'Изображение удалено. Загрузите новое.');
  };

  // Добавляем изображение и кнопку
  previewContainer.appendChild(img);
  previewContainer.appendChild(removeBtn);
  previewContainer.style.display = 'flex';

  // Сохраняем файл
  currentImageFile = file;

  // Уведомляем пользователя
  addMessageToChat('bot', 'Изображение загружено. Нажмите "Отправить", чтобы начать.');

});