// SEO management functionality
document.addEventListener('DOMContentLoaded', function() {
    const pageSelect = document.getElementById('page-select');
    const langSelect = document.getElementById('lang-select');
    const seoForm = document.getElementById('seo-form');
    const saveBtn = document.getElementById('save-seo-btn');
    const statusMessage = document.getElementById('status-message');
    
    const titleInput = document.getElementById('seo-title');
    const descriptionInput = document.getElementById('seo-description');
    const keywordsInput = document.getElementById('seo-keywords');
    
    const titleCounter = document.getElementById('title-counter');
    const descriptionCounter = document.getElementById('description-counter');
    const keywordsCounter = document.getElementById('keywords-counter');
    
    const previewTitle = document.getElementById('preview-title');
    const previewDescription = document.getElementById('preview-description');
    const htmlPreview = document.getElementById('html-preview');

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

    titleInput.addEventListener('input', () => updateCounter(titleInput, titleCounter, 60));
    descriptionInput.addEventListener('input', () => updateCounter(descriptionInput, descriptionCounter, 160));
    keywordsInput.addEventListener('input', () => updateCounter(keywordsInput, keywordsCounter, 255));

    // Preview updates
    function updatePreview() {
        previewTitle.textContent = titleInput.value || '{{ t.enter_title or "Enter title" }}';
        previewDescription.textContent = descriptionInput.value || '{{ t.enter_description or "Enter description" }}';
        
        htmlPreview.textContent = `<title>${titleInput.value || '{{ t.enter_title or "Enter title" }}'}</title>
<meta name="description" content="${descriptionInput.value || '{{ t.enter_description or "Enter description" }}'}">
<meta name="keywords" content="${keywordsInput.value || '{{ t.enter_keywords or "Enter keywords" }}'}">`;
    }

    titleInput.addEventListener('input', updatePreview);
    descriptionInput.addEventListener('input', updatePreview);
    keywordsInput.addEventListener('input', updatePreview);

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
        const formData = {
            page: pageSelect.value,
            lang: langSelect.value,
            seo: {
                title: titleInput.value,
                description: descriptionInput.value,
                keywords: keywordsInput.value
            }
        };

        try {
            const response = await fetch('/cms/api/seo', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
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
    pageSelect.addEventListener('change', loadSeoData);
    langSelect.addEventListener('change', loadSeoData);
    saveBtn.addEventListener('click', saveSeoData);

    // Load initial data
    loadSeoData();
});
