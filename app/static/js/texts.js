// Texts editor functionality
document.addEventListener('DOMContentLoaded', function() {
    const pageSelect = document.getElementById('page-select');
    const langSelect = document.getElementById('lang-select');
    const form = document.getElementById('texts-form');
    const notification = document.getElementById('notification');

    // Загрузить тексты при изменении страницы или языка
    function loadTexts() {
        const page = pageSelect.value;
        const lang = langSelect.value;
        
        fetch(`/cms/api/texts?page=${page}&lang=${lang}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Заполняем форму данными
                    document.getElementById('title').value = data.texts.title || '';
                    document.getElementById('subtitle').value = data.texts.subtitle || '';
                    document.getElementById('description').value = data.texts.description || '';
                    document.getElementById('cta_text').value = data.texts.cta_text || '';
                    document.getElementById('phone').value = data.texts.phone || '';
                    document.getElementById('address').value = data.texts.address || '';
                } else {
                    showNotification('Ошибка загрузки текстов: ' + data.message, 'error');
                }
            })
            .catch(error => {
                console.error('Ошибка:', error);
                showNotification('Ошибка загрузки текстов', 'error');
            });
    }

    // Сохранить тексты
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const page = pageSelect.value;
        const lang = langSelect.value;
        const formData = new FormData(form);
        const texts = {};
        
        // Собираем данные формы
        for (let [key, value] of formData.entries()) {
            texts[key] = value;
        }

        fetch('/cms/api/texts', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                page: page,
                lang: lang,
                texts: texts
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Тексты успешно сохранены', 'success');
            } else {
                showNotification('Ошибка сохранения: ' + data.message, 'error');
            }
        })
        .catch(error => {
            console.error('Ошибка:', error);
            showNotification('Ошибка сохранения текстов', 'error');
        });
    });

    // Загрузить тексты при изменении страницы или языка
    pageSelect.addEventListener('change', loadTexts);
    langSelect.addEventListener('change', loadTexts);

    // Показать уведомление
    function showNotification(message, type) {
        notification.className = `mt-4 p-4 rounded-md ${type === 'success' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'}`;
        notification.textContent = message;
        notification.classList.remove('hidden');
        
        setTimeout(() => {
            notification.classList.add('hidden');
        }, 5000);
    }

    // Загрузить тексты при загрузке страницы
    loadTexts();
});
