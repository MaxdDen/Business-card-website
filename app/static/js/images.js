// Функция для создания полей alt-текстов
function createAltTextFields(imageId) {
    const languages = window.supportedLanguages || ['en'];
    const fullNames = window.getLanguageFullNames ? window.getLanguageFullNames() : {'en': 'English'};
    
    let fieldsHTML = '';
    
    languages.forEach(lang => {
        const langName = fullNames[lang] || lang;
        const placeholder = `alt text: ${langName}`;
        
        fieldsHTML += `
            <div>
                <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1">${langName}</label>
                <input type="text" id="alt-${lang}-${imageId}" placeholder="${placeholder}" 
                    class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white">
            </div>
        `;
    });
    
    return fieldsHTML;
}

// Images management functionality
/*
 * Global variables 
 */
let images = {};
let translations = {};
let currentImageAlts = {};
const languages = window.supportedLanguages || ['en'];
const langNames = window.getLanguageNames ? window.getLanguageNames() : {'en': 'EN'};

// Initialize page
document.addEventListener('DOMContentLoaded', async function() {
    await loadTranslations();
    loadImages();
});

// Load translations from API
async function loadTranslations() {
    try {
        // Get current language from URL or default to 'en'
        const currentLang = getCurrentLanguage();
        
        const response = await fetch(`/cms/api/translations?lang=${currentLang}`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                translations = data.translations.images || {};
            } else {
                console.error('❌ Failed to load translations:', data.message);
            }
        } else {
            console.error('❌ Failed to load translations, status:', response.status);
        }
    } catch (error) {
        console.error('💥 Error loading translations:', error);
    }
}

// Get translation with fallback
function t(key, fallback = null) {
    return translations[key] || fallback || key;
}

// Get current language from URL
function getCurrentLanguage() {
    const path = window.location.pathname;
    const langMatch = path.match(/\/cms\/([a-z]{2})\//);
    return langMatch ? langMatch[1] : 'en';
}

// Load all images
async function loadImages() {
    
    try {
        const response = await fetch('/cms/api/images', {
            credentials: 'include'
        });
        
        if (!response.ok) {
            console.error('❌ API request failed with status:', response.status);
            const errorText = await response.text();
            console.error('❌ API error response:', errorText);
            showNotification(`API Error ${response.status}: ${errorText}`, 'error');
            return;
        }
        
        const data = await response.json();
        
        if (data.success) {
            images = {};
            data.images.forEach(image => {
                if (!images[image.type]) {
                    images[image.type] = [];
                }
                images[image.type].push(image);
            });
            
            renderImages();
        } else {
            console.error('❌ API returned error:', data.message);
            showNotification((translations.load_error || 'Load error') + ': ' + data.message, 'error');
        }
    } catch (error) {
        console.error('💥 Error loading images:', error);
        showNotification(translations.load_error || 'Load error', 'error');
    }
}

// Render images by type
function renderImages() {
    
    // Render image blocks for management
    renderImageBlocks();
    
    // Render gallery sections
    renderImageSections();
}

// Render image management blocks
function renderImageBlocks() {
    
    const blocksContainer = document.getElementById('imageBlocksContainer');
    if (!blocksContainer) {
        console.error('❌ Image blocks container not found');
        return;
    }
    
    // Clear existing content
    blocksContainer.innerHTML = '';
    
    // Get all images as a flat array
    const allImages = [];
    Object.keys(images).forEach(type => {
        images[type].forEach(image => {
            allImages.push({...image, type});
        });
    });
    
    // Create blocks for each image
    allImages.forEach(image => {
        const block = createImageBlock(image);
        blocksContainer.appendChild(block);
        
        // Добавляем поля alt-текстов динамически
        const altFieldsContainer = document.getElementById(`altFields-${image.id}`);
        if (altFieldsContainer) {
            altFieldsContainer.innerHTML = createAltTextFields(image.id);
        }
    });
    
    // Load alt texts for all images
    allImages.forEach(image => {
        loadAndDisplayAlts(image.id);
    });
}

// Render gallery sections (for viewing)
function renderImageSections() {
    
    // Get types dynamically from the images object
    const types = Object.keys(images);
    
    // Get the main container
    const mainContainer = document.getElementById('imagesContainer');
    if (!mainContainer) {
        console.error('❌ Main container not found');
        return;
    }
    
    // Clear existing content
    mainContainer.innerHTML = '';
    
    types.forEach(type => {
        const typeImages = images[type] || [];
        
        if (typeImages.length > 0) {
            // Setup drag and drop for ordered images
            const hasOrderedImages = typeImages.some(img => img.order !== undefined);
            if (hasOrderedImages) {
                setupDragAndDrop(type);
            }
        }
    });
}

// Populate image type select with dynamic options
function populateImageTypeSelect() {
    const select = document.getElementById('imageType');
    if (!select) {
        console.error('❌ Image type select not found');
        return;
    }
    
    // Clear existing options except the first one
    const firstOption = select.querySelector('option[value=""]');
    select.innerHTML = '';
    if (firstOption) {
        select.appendChild(firstOption);
    }
    
    // Get all unique types from images
    const types = Object.keys(images);
    
    // Add options for each type
    types.forEach(type => {
        const option = document.createElement('option');
        option.value = type;
        option.textContent = type.charAt(0).toUpperCase() + type.slice(1);
        select.appendChild(option);
    });
    
}

// Create image management block
function createImageBlock(image) {
    const block = document.createElement('div');
    block.className = 'bg-gray-50 dark:bg-gray-700 rounded-lg p-6 border border-gray-200 dark:border-gray-600';
    block.setAttribute('data-image-id', image.id);
    
    block.innerHTML = `
        <!-- Header -->
        <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-600 -mx-6 -mt-6 mb-6">
            <h3 class="text-lg font-medium text-gray-900 dark:text-white">
                ${image.type.charAt(0).toUpperCase() + image.type.slice(1)}
            </h3>
        </div>
        
        <div class="flex gap-6">
            <!-- Left side: Image preview and upload -->
            <div class="flex-shrink-0">
                <div class="w-48 h-32 border-2 border-dashed border-gray-300 dark:border-gray-500 rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-600">
                    <div id="imagePreview-${image.id}" class="w-full h-full flex items-center justify-center">
                        ${image.path && image.path.trim() !== '' && image.path !== 'optimized' ?
                            `<img src="/uploads/optimized/${image.path}" alt="${image.name}" class="w-full h-full object-cover">` :
                            `<div class="text-center text-gray-500 dark:text-gray-400">
                                <svg class="mx-auto h-8 w-8 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                                </svg>
                                <p class="text-xs">No image</p>
                            </div>`
                        }
                    </div>
                </div>
                <input type="file" id="fileInput-${image.id}" accept="image/*" class="hidden" onchange="handleImageUpload(${image.id}, this)">
            </div>
            
            <!-- Right side: Alt texts -->
            <div class="flex-1">
                <div class="mb-4">
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Alt Texts
                    </label>
                    <div class="space-y-3" id="altFields-${image.id}">
                        <!-- Поля будут добавлены динамически -->
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Bottom controls -->
        <div class="flex justify-between items-center mt-4 pt-4 border-t border-gray-200 dark:border-gray-600">
            <!-- Left side: Control buttons -->
            <div class="flex space-x-2">
                <button onclick="triggerImageUpload(${image.id})" 
                    class="px-3 py-1 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500">
                    <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                    </svg>
                    ${t('change', 'Change')}
                </button>
                <button onclick="deleteImage(${image.id})" 
                    class="px-3 py-1 text-sm bg-red-600 text-white rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500">
                    <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                    </svg>
                    ${t('delete', 'Delete')}
                </button>
            </div>
            
            <!-- Right side: Save button -->
            <button onclick="saveImageData(${image.id})" 
                class="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500">
                <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                </svg>
                ${t('save', 'Save')}
            </button>
        </div>
    `;
    
    return block;
}

// Trigger image upload
function triggerImageUpload(imageId) {
    const fileInput = document.getElementById(`fileInput-${imageId}`);
    if (fileInput) {
        fileInput.click();
    }
}

// Handle image upload
async function handleImageUpload(imageId, fileInput) {
    const file = fileInput.files[0];
    if (!file) return;
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('image_id', imageId);
        
        const response = await fetch('/cms/api/images/update', {
            method: 'POST',
            body: formData,
            credentials: 'include'
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                // Update preview
                updateImagePreview(imageId, data.image.path);
                showNotification(t('image_updated', 'Image updated successfully'), 'success');
                
                // Reload images
                loadImages();
            } else {
                showNotification(t('update_failed', 'Failed to update image') + ': ' + data.message, 'error');
            }
        } else {
            const errorText = await response.text();
            console.error('Upload failed:', response.status, errorText);
            showNotification(t('upload_failed', 'Upload failed') + ': ' + response.status, 'error');
        }
    } catch (error) {
        console.error('Upload error:', error);
        showNotification(t('upload_error', 'Upload error') + ': ' + error.message, 'error');
    }
}

// Update image preview
function updateImagePreview(imageId, imagePath) {
    const preview = document.getElementById(`imagePreview-${imageId}`);
    
    if (preview && imagePath && imagePath.trim() !== '') {
        // Проверяем, что путь не содержит только 'optimized'
        if (imagePath === 'optimized' || imagePath === '/optimized') {
            console.error('Invalid image path:', imagePath);
            return;
        }
        
        const imageUrl = `/uploads/optimized/${imagePath}`;
        preview.innerHTML = `<img src="${imageUrl}" alt="Preview" class="w-full h-full object-cover">`;
    } else {
        console.log('Preview element not found or imagePath is empty');
    }
}

// Save image data (alt texts and image info)
async function saveImageData(imageId) {
    
    try {
        // Collect alt texts динамически
        const languages = window.supportedLanguages || ['en', 'ru', 'ua'];
        const alts = {};
        
        languages.forEach(lang => {
            const input = document.getElementById(`alt-${lang}-${imageId}`);
            if (input) {
                alts[lang] = input.value || '';
            }
        });
        
        // Save alt texts
        const altsResponse = await fetch(`/cms/api/images/${imageId}/alts`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({alts: alts}),
            credentials: 'include'
        });
        
        if (!altsResponse.ok) {
            showNotification('Failed to save alt texts: ' + altsResponse.status, 'error');
            return;
        }
        
        const altsData = await altsResponse.json();
        if (!altsData.success) {
            showNotification('Failed to save alt texts: ' + altsData.message, 'error');
            return;
        }
        
        // Update image record in database
        const imageResponse = await fetch(`/cms/api/images/${imageId}/update`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                // We can add other fields here if needed in the future
                updated: true
            }),
            credentials: 'include'
        });
        
        if (!imageResponse.ok) {
            showNotification('Failed to update image record: ' + imageResponse.status, 'error');
            return;
        }
        
        const imageData = await imageResponse.json();
        if (!imageData.success) {
            showNotification('Failed to update image record: ' + imageData.message, 'error');
            return;
        }
        
        showNotification(t('image_data_saved', 'Image data saved successfully'), 'success');
        
        // Reload images to reflect changes
        loadImages();
        
    } catch (error) {
        console.error('Save error:', error);
        showNotification(t('save_error', 'Save error') + ': ' + error.message, 'error');
    }
}

// Setup drag and drop for slider
function setupDragAndDrop(type) {
    const grid = document.getElementById(type + 'Grid');
    if (!grid) return;
    
    grid.addEventListener('dragstart', function(e) {
        e.dataTransfer.setData('text/plain', e.target.closest('[data-id]').dataset.id);
        e.target.style.opacity = '0.5';
    });
    
    grid.addEventListener('dragover', function(e) {
        e.preventDefault();
    });
    
    grid.addEventListener('drop', function(e) {
        e.preventDefault();
        const draggedId = e.dataTransfer.getData('text/plain');
        const target = e.target.closest('[data-id]');
        
        if (target && target.dataset.id !== draggedId) {
            moveImageOrder(draggedId, target.dataset.id);
        }
    });
    
    grid.addEventListener('dragend', function(e) {
        e.target.style.opacity = '1';
    });
}

// Delete image
async function deleteImage(imageId) {
    if (!confirm(t('confirm_delete', 'Are you sure you want to delete this image?'))) {
        return;
    }
    
    try {
        const response = await fetch(`/cms/api/images/${imageId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification(t('image_deleted', 'Image deleted successfully'), 'success');
            loadImages(); // Reload images
        } else {
            showNotification(result.message || t('delete_error', 'Delete error'), 'error');
        }
    } catch (error) {
        console.error('Delete error:', error);
        showNotification(t('delete_error', 'Delete error'), 'error');
    }
}

// Move image up/down
async function moveImage(imageId, direction) {
    try {
        const response = await fetch(`/cms/api/images/${imageId}/move`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ direction })
        });
        
        const result = await response.json();
        
        if (result.success) {
            loadImages(); // Reload images
        } else {
            showNotification(result.message || t('move_error', 'Move error'), 'error');
        }
    } catch (error) {
        console.error('Move error:', error);
        showNotification(t('move_error', 'Move error'), 'error');
    }
}

// Move image order (drag and drop)
async function moveImageOrder(draggedId, targetId) {
    try {
        const response = await fetch(`/cms/api/images/${draggedId}/move-to`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ target_id: targetId })
        });
        
        const result = await response.json();
        
        if (result.success) {
            loadImages(); // Reload images
        } else {
            showNotification(result.message || t('move_error', 'Move error'), 'error');
        }
    } catch (error) {
        console.error('Move error:', error);
        showNotification(t('move_error', 'Move error'), 'error');
    }
}

// Show notification
function showNotification(message, type) {
    const notification = document.getElementById('notification');
    notification.className = `mt-4 p-4 rounded-md ${type === 'success' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'}`;
    notification.textContent = message;
    notification.classList.remove('hidden');
    
    setTimeout(() => {
        notification.classList.add('hidden');
    }, 5000);
}

// Alt-text management functions
async function loadImageAlts(imageId) {
    try {
        const response = await fetch(`/cms/api/images/${imageId}/alts`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                currentImageAlts = data.alts;
                return data.alts;
            }
        }
        return {};
    } catch (error) {
        console.error('Error loading image alts:', error);
        return {};
    }
}

async function saveImageAlts(imageId, alts) {
    try {
        const response = await fetch(`/cms/api/images/${imageId}/alts`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({ alts })
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                showNotification(t('alts_saved', 'Alt-тексты сохранены'), 'success');
                return true;
            } else {
                showNotification(data.message || t('alts_save_error', 'Ошибка сохранения alt-текстов'), 'error');
            }
        } else {
            showNotification(t('alts_save_error', 'Ошибка сохранения alt-текстов'), 'error');
        }
    } catch (error) {
        console.error('Error saving image alts:', error);
        showNotification(t('alts_save_error', 'Ошибка сохранения alt-текстов'), 'error');
    }
    return false;
}

function showAltTextModal(imageId, imageName) {
    // Create modal for editing alt texts
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
    modal.innerHTML = `
        <div class="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4">
            <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-4">
                ${t('alts_for', 'Alt-тексты для')}: ${imageName}
            </h3>
            <div id="altTextsContainer" class="space-y-4">
                <!-- Alt texts will be loaded here -->
            </div>
            <div class="flex justify-end space-x-3 mt-6">
                <button onclick="closeAltTextModal()" class="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200">
                    ${t('cancel', 'Отмена')}
                </button>
                <button onclick="saveAltTexts(${imageId})" class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
                    ${t('save', 'Сохранить')}
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Load current alt texts
    loadImageAlts(imageId).then(alts => {
        const container = document.getElementById('altTextsContainer');
        const languages = window.supportedLanguages || ['en', 'ru', 'ua'];
        const fullNames = window.getLanguageFullNames ? window.getLanguageFullNames() : {
            'ru': 'Русский', 'en': 'English', 'ua': 'Українська'
        };
        
        languages.forEach(lang => {
            const langName = fullNames[lang] || lang;
            const placeholder = lang === 'ru' ? t('enter_alt_ru', 'Введите alt-текст') : 
                              lang === 'en' ? t('enter_alt_en', 'Enter alt text') : 
                              lang === 'ua' ? t('enter_alt_ua', 'Введіть alt-текст') : 
                              t('enter_alt_en', 'Enter alt text');
            
            container.innerHTML += `
                <div>
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        ${langName}
                    </label>
                    <input type="text" 
                           id="alt_${lang}" 
                           value="${alts[lang] || ''}" 
                           class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                           placeholder="${placeholder}">
                </div>
            `;
        });
    });
}

function closeAltTextModal() {
    const modal = document.querySelector('.fixed.inset-0');
    if (modal) {
        modal.remove();
    }
}

async function saveAltTexts(imageId) {
    const alts = {};
    const languages = window.supportedLanguages || ['en', 'ru', 'ua'];
    
    languages.forEach(lang => {
        const input = document.getElementById(`alt_${lang}`);
        if (input && input.value.trim()) {
            alts[lang] = input.value.trim();
        }
    });
    
    const success = await saveImageAlts(imageId, alts);
    if (success) {
        closeAltTextModal();
        loadImages(); // Reload images to show updated alts
    }
}

async function loadAndDisplayAlts(imageId) {
    try {
        const alts = await loadImageAlts(imageId);
        
        // Update gallery display
        const container = document.getElementById(`alt-display-${imageId}`);
        if (container) {
            const languages = window.supportedLanguages || ['en', 'ru', 'ua'];
            const langNames = window.getLanguageNames ? window.getLanguageNames() : {
                'ru': 'RU', 'en': 'EN', 'ua': 'UA'
            };
            
            container.innerHTML = languages.map(lang => {
                const altText = alts[lang] || '';
                const displayText = altText ? altText.substring(0, 30) + (altText.length > 30 ? '...' : '') : t('not_set', 'Не задано');
                return `<div><span class="text-gray-500">${langNames[lang]}:</span> ${displayText}</div>`;
            }).join('');
        }
        
        // Update management form fields
        const languages = window.supportedLanguages || ['en', 'ru', 'ua'];
        languages.forEach(lang => {
            const input = document.getElementById(`alt-${lang}-${imageId}`);
            if (input) {
                input.value = alts[lang] || '';
            }
        });
    } catch (error) {
        console.error('Error loading alts for image:', imageId, error);
    }
}
