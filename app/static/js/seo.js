// SEO management functionality
document.addEventListener('DOMContentLoaded', function() {
    const pageSelect = document.getElementById('page-select');
    const langSelect = document.getElementById('lang-select');
    const seoForm = document.getElementById('seo-form');
    const saveBtn = document.getElementById('save-seo-btn');
    const statusMessage = document.getElementById('status-message');
    const dynamicSeoContainer = document.getElementById('dynamic-seo-container');
    const dynamicSeoFields = document.getElementById('dynamic-seo-fields');
    
    const previewTitle = document.getElementById('preview-title');
    const previewDescription = document.getElementById('preview-description');
    const htmlPreview = document.getElementById('html-preview');

    // Загрузить динамические SEO поля
    function loadDynamicSeoFields() {
        const page = pageSelect.value;
        const lang = langSelect.value;
        
        // Показываем индикатор загрузки
        showSeoLoadingState();
        
        fetch(`/cms/api/dynamic-fields?page=${page}&lang=${lang}&field_type=seo`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    renderDynamicSeoFields(data.fields);
                    hideSeoLoadingState();
                } else {
                    showSeoErrorState(data.message || 'Ошибка загрузки SEO полей');
                }
            })
            .catch(error => {
                console.error('Ошибка:', error);
                showSeoErrorState('Ошибка загрузки SEO полей');
            });
    }

    // Показать состояние загрузки SEO
    function showSeoLoadingState() {
        dynamicSeoContainer.innerHTML = `
            <div class="text-center py-8 text-gray-500 dark:text-gray-400">
                <svg class="animate-spin mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <p class="mt-2">Загрузка SEO полей...</p>
            </div>
        `;
    }

    // Скрыть состояние загрузки SEO
    function hideSeoLoadingState() {
        seoForm.classList.remove('hidden');
        dynamicSeoContainer.style.display = 'none';
    }

    // Показать состояние ошибки SEO
    function showSeoErrorState(message) {
        dynamicSeoContainer.innerHTML = `
            <div class="text-center py-8 text-red-500">
                <svg class="mx-auto h-12 w-12 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
                </svg>
                <p class="mt-2">${message}</p>
                <button onclick="loadDynamicSeoFields()" class="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
                    Попробовать снова
                </button>
            </div>
        `;
    }

    // Отрендерить динамические SEO поля
    function renderDynamicSeoFields(fields) {
        if (fields.length === 0) {
            dynamicSeoFields.innerHTML = `
                <div class="text-center py-8 text-gray-500 dark:text-gray-400">
                    <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                    </svg>
                    <p class="mt-2">SEO поля не найдены</p>
                    <p class="text-sm">Добавьте SEO переменные в шаблоны или синхронизируйте их</p>
                </div>
            `;
            return;
        }

        let fieldsHTML = '';
        fields.forEach(field => {
            const required = field.required ? ' <span class="text-red-500">*</span>' : '';
            const fieldId = `seo-${field.key}`;
            const maxLength = field.key === 'meta_title' ? 60 : field.key === 'meta_description' ? 160 : 255;
            
            fieldsHTML += `
                <div>
                    <label for="${fieldId}" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        ${field.label}${required}
                    </label>
                    ${field.type === 'textarea' ? `
                        <textarea id="${fieldId}" name="${field.key}" rows="3" maxlength="${maxLength}"
                                  class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                                  placeholder="${field.placeholder}">${field.value}</textarea>
                    ` : `
                        <input type="text" id="${fieldId}" name="${field.key}" maxlength="${maxLength}"
                               class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                               placeholder="${field.placeholder}" value="${field.value}">
                    `}
                    <div class="mt-1 text-sm text-gray-500 dark:text-gray-400">
                        <span id="${fieldId}-counter">${field.value.length}</span>/${maxLength} символов
                    </div>
                </div>
            `;
        });

        dynamicSeoFields.innerHTML = fieldsHTML;
        
        // Добавляем обработчики для счетчиков символов и превью
        setupSeoFieldHandlers();
    }

    // Настроить обработчики для SEO полей
    function setupSeoFieldHandlers() {
        const titleField = document.getElementById('seo-meta_title');
        const descriptionField = document.getElementById('seo-meta_description');
        
        if (titleField) {
            titleField.addEventListener('input', updateSeoPreview);
            titleField.addEventListener('input', () => updateCounter(titleField, document.getElementById('seo-meta_title-counter'), 60));
        }
        
        if (descriptionField) {
            descriptionField.addEventListener('input', updateSeoPreview);
            descriptionField.addEventListener('input', () => updateCounter(descriptionField, document.getElementById('seo-meta_description-counter'), 160));
        }
    }

    // Character counters
    function updateCounter(input, counter, maxLength) {
        const length = input.value.length;
        counter.textContent = length;
        if (length > maxLength * 0.9) {
            counter.classList.add('text-red-500');
        } else {
            counter.classList.remove('text-red-500');
        }
    }

    // Preview updates для динамических полей
    function updateSeoPreview() {
        const titleField = document.getElementById('seo-meta_title');
        const descriptionField = document.getElementById('seo-meta_description');
        const keywordsField = document.getElementById('seo-meta_keywords');
        
        const title = titleField ? titleField.value : '';
        const description = descriptionField ? descriptionField.value : '';
        const keywords = keywordsField ? keywordsField.value : '';
        
        if (previewTitle) {
            previewTitle.textContent = title || 'Введите заголовок';
        }
        if (previewDescription) {
            previewDescription.textContent = description || 'Введите описание';
        }
        
        if (htmlPreview) {
            htmlPreview.textContent = `<title>${title || 'Введите заголовок'}</title>
<meta name="description" content="${description || 'Введите описание'}">
<meta name="keywords" content="${keywords || 'Введите ключевые слова'}">`;
        }
    }

    // Load SEO data
    async function loadSeoData() {
        try {
            const response = await fetch(`/cms/api/seo?page=${pageSelect.value}&lang=${langSelect.value}`);
            const data = await response.json();
            
            if (data.success) {
                titleInput.value = data.seo.title || '';
                descriptionInput.value = data.seo.description || '';
                keywordsInput.value = data.seo.keywords || '';
                updatePreview();
                updateCounter(titleInput, titleCounter, 60);
                updateCounter(descriptionInput, descriptionCounter, 160);
                updateCounter(keywordsInput, keywordsCounter, 255);
            } else {
                showStatus('error', data.message);
            }
        } catch (error) {
            console.error('Ошибка загрузки SEO данных:', error);
                showStatus('error', '{{ t.load_error or "Load error" }}');
        }
    }

    // Save SEO data
    async function saveSeoData() {
        // Собираем данные из динамических полей
        const seoData = {};
        const form = document.getElementById('seo-form');
        const formData = new FormData(form);
        
        for (let [key, value] of formData.entries()) {
            seoData[key] = value;
        }

        const requestData = {
            page: pageSelect.value,
            lang: langSelect.value,
            seo: seoData
        };

        try {
            const response = await fetch('/cms/api/seo', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });
            
            const data = await response.json();
            
            if (data.success) {
                showStatus('success', '{{ t.seo_saved or "SEO data saved successfully" }}');
            } else {
                showStatus('error', data.message);
            }
        } catch (error) {
            console.error('Ошибка сохранения SEO данных:', error);
            showStatus('error', '{{ t.save_error or "Save error" }}');
        }
    }

    // Show status message
    function showStatus(type, message) {
        statusMessage.className = `mt-4 p-4 rounded-md ${type === 'success' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'}`;
        statusMessage.textContent = message;
        statusMessage.classList.remove('hidden');
        
        setTimeout(() => {
            statusMessage.classList.add('hidden');
        }, 5000);
    }

    // Event listeners
    pageSelect.addEventListener('change', loadDynamicSeoFields);
    langSelect.addEventListener('change', loadDynamicSeoFields);
    seoForm.addEventListener('submit', function(e) {
        e.preventDefault();
        saveSeoData();
    });

    // Load initial data
    loadDynamicSeoFields();
});
