document.addEventListener('DOMContentLoaded', function() {
    // Подключение к WebSocket-серверу
    const ws = new WebSocket("https://noncontinuably-meatier-ardella.ngrok-free.dev");

    // Попробуем получить элементы. Если их нет, getElementById вернёт null.
    const messagesContainer = document.getElementById('messages');
    const messageInput = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendButton');

    // Проверяем, существуют ли необходимые элементы в DOM
    if (!messagesContainer) {
        console.error("Элемент с id 'messages' не найден в DOM.");
        // Если контейнер сообщений не найден, дальнейшая логика чата бессмысленна
        return;
    }
    if (!messageInput) {
        console.error("Элемент с id 'messageInput' не найден в DOM.");
        // Если поле ввода не найдено, отправка сообщений невозможна
        return;
    }
    if (!sendButton) {
        console.error("Элемент с id 'sendButton' не найден в DOM.");
        // Если кнопка отправки не найдена, отправка сообщений невозможна
        return;
    }

    // Обработчик отправки сообщения
    function sendMessage() {
        const text = messageInput.value.trim();
        if (!text) return; // Не отправляем пустые сообщения

        // Отправляем сообщение на сервер
        ws.send(JSON.stringify({
            text: text,
            sender: 'user' // Предполагаем, что это сообщение пользователя
        }));

        // Очищаем поле ввода после отправки
        messageInput.value = '';
    }

    // Обработка нажатия клавиши Enter в поле ввода
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    // Обработка клика по кнопке отправки
    sendButton.addEventListener('click', sendMessage);

    // Обработчик открытия соединения WebSocket
    ws.onopen = () => {
        console.log("Соединение с WebSocket-сервером установлено.");
        // Отправляем имя пользователя при подключении
        ws.send(JSON.stringify({ username: "Аноним" }));
    };

    // Обработчик получения сообщения от сервера
    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);

            // Проверяем структуру данных
            if (!data || typeof data.text !== 'string') {
                console.error("Некорректные данные от сервера:", event.data);
                return;
            }

            // Создаём элемент для нового сообщения
            const div = document.createElement('div');
            div.classList.add('message');
            // Определяем класс сообщения в зависимости от отправителя
            // Если data.sender === 'user', то класс 'user-message', иначе 'support-message'
            div.classList.add(data.sender === 'user' ? 'user-message' : 'support-message');

            // Создаём элемент для имени отправителя
            const senderName = document.createElement('div');
            senderName.classList.add('sender-name');
            // Используем data.name, если оно есть, иначе можно вывести 'Аноним' или другое значение
            senderName.textContent = data.name || 'Аноним';

            // Создаём элемент для текста сообщения
            const messageText = document.createElement('div');
            messageText.classList.add('message-text');
            messageText.textContent = data.text;

            // Собираем элементы сообщения
            div.appendChild(senderName);
            div.appendChild(messageText);

            // Добавляем сообщение в контейнер (messagesContainer уже проверен на null)
            messagesContainer.appendChild(div);

            // Прокручиваем контейнер до последнего сообщения
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        } catch (error) {
            console.error("Ошибка при обработке входящего сообщения:", error);
            console.error("Сырые данные:", event.data);
        }
    };

    // Обработчик ошибок WebSocket
    ws.onerror = (error) => {
        console.error("WebSocket ошибка:", error);
    };

    // Обработчик закрытия соединения WebSocket
    ws.onclose = () => {
        console.warn("Соединение с WebSocket-сервером закрыто.");
        // Создаём сообщение о потере соединения
        const div = document.createElement('div');
        div.classList.add('system-message');
        div.textContent = "Соединение с сервером потеряно.";

        // Добавляем сообщение в контейнер (messagesContainer уже проверен на null)
        messagesContainer.appendChild(div);

        // Прокручиваем контейнер до последнего сообщения
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    };
});