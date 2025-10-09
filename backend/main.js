const API_BASE_URL = "https://noncontinuously-meatier-ardella.ngrok-free.dev";

fetch(`${API_BASE_URL}/api/account?initData=` + encodeURIComponent(initData))


  // или другой URL

document.addEventListener('DOMContentLoaded', function () {
    const switchEl = document.getElementById('toggleSwitch');
    const labelEl = document.getElementById('toggleLabel');
    let isActive = false;

    switchEl.addEventListener('click', () => {
        isActive = !isActive;

        if (isActive) {
            switchEl.classList.add('active');
            labelEl.textContent = 'Включить';
            labelEl.classList.remove('off');
        } else {
            switchEl.classList.remove('active');
            labelEl.textContent = 'Включить';
            labelEl.classList.add('off');
        }

    });
});
document.addEventListener('DOMContentLoaded', function () {
    const buttons = document.querySelectorAll('.sixth_screen_selector_btn');

    // Загружаем сохранённые активные кнопки
    const savedActiveButtons = JSON.parse(localStorage.getItem('activeButtons')) || [];

    buttons.forEach(button => {
        // Если кнопка была активной — добавляем класс
        if (savedActiveButtons.includes(button.textContent)) {
            button.classList.add('active');
        }

        button.addEventListener('click', () => {
            // Переключаем состояние кнопки
            button.classList.toggle('active');

            // Получаем все активные кнопки
            const activeButtons = Array.from(buttons)
                .filter(btn => btn.classList.contains('active'))
                .map(btn => btn.textContent);

            // Сохраняем в localStorage
            localStorage.setItem('activeButtons', JSON.stringify(activeButtons));
        });
    });
});
const ws = new WebSocket("wss://noncontinuously-meatier-ardella.ngrok-free.dev");
    const messages = document.getElementById('messages');
    const messageInput = document.getElementById('messageInput');
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        const div = document.createElement('div');
        div.classList.add('message');
        div.classList.add(data.sender === 'user' ? 'user-message' : 'support-message');
        div.textContent = data.text;
        messages.appendChild(div);
        messages.scrollTop = messages.scrollHeight;
        };

    function sendMessage() {
        const text = messageInput.value.trim();
        if (!text) return;
            ws.send(JSON.stringify({
                text: text,
                sender: 'user'
            }));

        messageInput.value = '';
        }

    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
                sendMessage();
            }
});

const WebApp = window.Telegram.WebApp;

        // Загрузка данных аккаунта
    async function loadAccount() {
        const initData = WebApp.initData;
        if (!initData) {
            alert("Не удалось получить данные Telegram");
            return;
        }

        try {
            const response = await fetch(`/api/account?initData=${encodeURIComponent(initData)}`);
            const data = await response.json();

            if (response.ok) {
                document.getElementById('firstName').value = data.first_name;
                document.getElementById('lastName').value = data.last_name;
                document.getElementById('phone').value = data.phone_number || '';
                document.getElementById('avatarPreview').src = data.photo_url || 'https://via.placeholder.com/100';
            } else {
                console.error("Ошибка загрузки аккаунта:", data);
            }
        } catch (error) {
            console.error("Ошибка:", error);
            }
        }

        // Сохранение аккаунта
        async function saveAccount() {
            const initData = WebApp.initData;
            const phone = document.getElementById('phone').value;

            if (!initData) {
                alert("Не удалось получить данные Telegram");
                return;
            }

            try {
                const response = await fetch('/api/account', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        initData: initData,
                        phone_number: phone
                    })
                });

                if (response.ok) {
                    alert("Данные сохранены!");
                } else {
                    const error = await response.json();
                    alert("Ошибка: " + error.error);
                }
            } catch (error) {
                console.error("Ошибка:", error);
                alert("Произошла ошибка при сохранении");
            }
        }

        // Загружаем данные при открытии
        document.addEventListener('DOMContentLoaded', loadAccount);