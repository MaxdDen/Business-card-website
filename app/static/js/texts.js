// Texts editor functionality
document.addEventListener('DOMContentLoaded', function() {
    const pageSelect = document.getElementById('page-select');
    const langSelect = document.getElementById('lang-select');
    const form = document.getElementById('texts-form');
    const notification = document.getElementById('notification');
    const dynamicFieldsContainer = document.getElementById('dynamic-fields-container');
    const dynamicFieldsForm = document.getElementById('dynamic-fields-form');

    // Загрузить динамические поля при изменении страницы или языка
    function loadDynamicFields() {
        const page = pageSelect.value;
        const lang = langSelect.value;
        
        // Показываем индикатор загрузки
        showLoadingState();
        
        fetch(`/cms/api/dynamic-fields?page=${page}&lang=${lang}&field_type=texts`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    renderDynamicFields(data.fields);
                    hideLoadingState();
                } else {
                    showErrorState(data.message || 'Ошибка загрузки полей');
                }
            })
            .catch(error => {
                console.error('Ошибка:', error);
                showErrorState('Ошибка загрузки полей');
            });
    }

    // Показать состояние загрузки
    function showLoadingState() {
        dynamicFieldsContainer.innerHTML = `
            <div class="text-center py-8 text-gray-500 dark:text-gray-400">
                <svg class="animate-spin mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <p class="mt-2">Загрузка полей...</p>
            </div>
        `;
    }

    // Скрыть состояние загрузки
    function hideLoadingState() {
        form.classList.remove('hidden');
        dynamicFieldsContainer.style.display = 'none';
    }

    // Показать состояние ошибки
    function showErrorState(message) {
        dynamicFieldsContainer.innerHTML = `
            <div class="text-center py-8 text-red-500">
                <svg class="mx-auto h-12 w-12 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
                </svg>
                <p class="mt-2">${message}</p>
                <button onclick="loadDynamicFields()" class="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
                    Попробовать снова
                </button>
            </div>
        `;
    }

    // Отрендерить динамические поля
    function renderDynamicFields(fields) {
        if (fields.length === 0) {
            dynamicFieldsForm.innerHTML = `
                <div class="text-center py-8 text-gray-500 dark:text-gray-400">
                    <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                    </svg>
                    <p class="mt-2">Поля для редактирования не найдены</p>
                    <p class="text-sm">Добавьте переменные в шаблоны или синхронизируйте их</p>
                </div>
            `;
            return;
        }

        let fieldsHTML = '';
        fields.forEach(field => {
            const required = field.required ? ' <span class="text-red-500">*</span>' : '';
            const fieldId = `field-${field.key}`;
            
            if (field.type === 'textarea') {
                fieldsHTML += `
                    <div>
                        <label for="${fieldId}" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            ${field.label}${required}
                        </label>
                        <textarea id="${fieldId}" name="${field.key}" rows="4" 
                                  class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                                  placeholder="${field.placeholder}">${field.value}</textarea>
                    </div>
                `;
            } else {
                fieldsHTML += `
                    <div>
                        <label for="${fieldId}" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            ${field.label}${required}
                        </label>
                        <input type="text" id="${fieldId}" name="${field.key}" 
                               class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                               placeholder="${field.placeholder}" value="${field.value}">
                    </div>
                `;
            }
        });

        dynamicFieldsForm.innerHTML = fieldsHTML;
    }

    // Загрузить тексты при изменении страницы или языка (старая функция для совместимости)
    function loadTexts() {
        loadDynamicFields();
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
    pageSelect.addEventListener('change', loadDynamicFields);
    langSelect.addEventListener('change', loadDynamicFields);

    // Показать уведомление
    function showNotification(message, type) {
        notification.className = `mt-4 p-4 rounded-md ${type === 'success' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'}`;
        notification.textContent = message;
        notification.classList.remove('hidden');
        
        setTimeout(() => {
            notification.classList.add('hidden');
        }, 5000);
    }

    // Загрузить динамические поля при загрузке страницы
    loadDynamicFields();
});
