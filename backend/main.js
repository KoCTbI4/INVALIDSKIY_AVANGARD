//=====================================================----------------------------------СТРАНИЦА УВЕДОМЛЕНИЙ----------------==============================================
//                       ПО БОЛЬШЕЙ ЧАСТИ ПРОСТО АНИМАЦИЯ, НИКАКОГО ДОПОЛНЕНИЯ ФУНКЦИОНАЛА ПРИЛОЖЕНИЯ
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

//=======================-----------------------------------------СТРАНИЦА ПРИСВОЕНИЯ ДИАГНОЗА, ФУНКЦИЯ СЧИТЫВАНИЯ ВЫБОРА И ПРИСВОЕНИЕ ДИАГНОЗА-----------=========================================================

document.addEventListener('DOMContentLoaded', function () {
    const buttons = document.querySelectorAll('.sixth_screen_selector_btn');
    const nextButton = document.getElementById('next-btn');

    // Загружаем сохранённые активные методы из localStorage
    const savedMethods = JSON.parse(localStorage.getItem('userCommunicationMethods')) || [];

    // Если есть сохранённые методы — подсвечиваем соответствующие кнопки
    buttons.forEach(button => {
        if (savedMethods.includes(button.dataset.method)) {
            button.classList.add('active');
        }
    });

    // Массив для хранения выбранных методов
    let selectedMethods = [...savedMethods];

    // Обработчик кликов по кнопкам
    buttons.forEach(button => {
        button.addEventListener('click', () => {
            // Переключаем состояние кнопки
            button.classList.toggle('active');

            // Добавляем или удаляем метод из массива
            if (button.classList.contains('active')) {
                selectedMethods.push(button.dataset.method);
            } else {
                selectedMethods = selectedMethods.filter(method => method !== button.dataset.method);
            }

            // Удаляем дубликаты и сортируем методы для последовательности
            selectedMethods = [...new Set(selectedMethods)].sort();

            // Сохраняем выбранные методы в localStorage
            localStorage.setItem('userCommunicationMethods', JSON.stringify(selectedMethods));
        });
    });

    // Обработчик кнопки "Далее"
    nextButton.addEventListener('click', () => {
        if (selectedMethods.length === 0) {
            alert('Пожалуйста, выберите хотя бы один метод общения.');
            return;
        }

        // Формируем ключ для switch из выбранных методов
        const methodsKey = selectedMethods.join('-'); // Например: "text-gestures"

        // Определяем диагноз через switch
        let diagnosis = '';
        switch (methodsKey) {
            case 'text':
                diagnosis = 'Слабослышащий / Невербальный';
                break;
            case 'gestures':
                diagnosis = 'Глухой / Использует жестовый язык';
                break;
            case 'voice':
                diagnosis = 'Говорящий / Голосовой контакт';
                break;
            case 'text':
            case 'gestures':
                diagnosis = 'Комбинированный тип: Текст + Жесты';
                break;
            case 'text':
            case 'voice':
                diagnosis = 'Комбинированный тип: Текст + Голос';
                break;
            case 'gestures':
            case 'voice':
                diagnosis = 'Комбинированный тип: Жесты + Голос';
                break;
            case 'text':
            case 'gestures':
            case 'voice':
                diagnosis = 'Многофункциональный тип: Текст + Жесты + Голос';
                break;
            default:
                diagnosis = 'Неопределённый тип коммуникации';
        }

        // Сохраняем диагноз в localStorage
        localStorage.setItem('userDiagnosis', JSON.stringify({ diagnosis }));
        localStorage.setItem('onboarded', 'true');

        // Переходим на следующую страницу
        window.location.href = 'input_user_data.html';
    });
});


//=========================================================---------------------РУДИМЕНТ СТАРОЙ ИДЕИ--------------------========================================
 // писька
//====================================------------------------------------------------ЧАТ С ПРОСТЫМ ОПИСАНИЕМ ИЗОБРАЖЕНИЯ------------------------========================================
//                              BLIP MODEL (ТУПЕЕ ЧЕМ MOONDREAM)
// Загружаем данные при открытии
document.addEventListener('DOMContentLoaded', loadAccount);

const uploadInput = document.getElementById('imageUpload');
const preview = document.getElementById('preview');
const chat = document.getElementById('chat');

uploadInput.addEventListener('change', async (e) => {
  const file = e.target.files[0];
  if (!file) return;

  // Показываем превью
  const img = document.createElement('img');
  img.src = URL.createObjectURL(file);
  preview.innerHTML = '';
  preview.appendChild(img);

  // Отправляем изображение на бэкенд
  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await fetch('http://localhost:8000/api/describe', {
      method: 'POST',
      body: formData,
    });

    const data = await response.json();
    const description = data.description;

    // Добавляем сообщение в чат
    addMessageToChat('bot', description);

    // Озвучиваем результат (если поддерживается)
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(description);
      speechSynthesis.speak(utterance);
    }
  } catch (error) {
    console.error('Ошибка:', error);
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