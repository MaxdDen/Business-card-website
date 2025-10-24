// Images management functionality
// Global variables
let images = {};

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    loadImages();
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    // Upload form
    document.getElementById('uploadForm').addEventListener('submit', handleUpload);
    
    // File input change
    document.getElementById('imageFile').addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            // Validate file size (2MB max)
            if (file.size > 2 * 1024 * 1024) {
                showNotification('{{ t.file_too_large or "File too large. Max size: 2MB" }}', 'error');
                e.target.value = '';
                return;
            }
            
            // Validate file type
            const allowedTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/x-icon'];
            if (!allowedTypes.includes(file.type)) {
                showNotification('{{ t.unsupported_format or "Unsupported file format. Allowed: JPG, PNG, WebP, ICO" }}', 'error');
                e.target.value = '';
                return;
            }
        }
    });
}

// Load all images
async function loadImages() {
    try {
        const response = await fetch('/cms/api/images');
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
            showNotification('{{ t.load_error or "Load error" }}: ' + data.message, 'error');
        }
    } catch (error) {
        console.error('Error loading images:', error);
        showNotification('{{ t.load_error or "Load error" }}', 'error');
    }
}

// Render images by type
function renderImages() {
    const types = ['logo', 'slider', 'background', 'favicon'];
    
    types.forEach(type => {
        const container = document.getElementById(type + 'Images');
        const typeImages = images[type] || [];
        
        if (typeImages.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8 text-gray-500 dark:text-gray-400">
                    <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                    </svg>
                    <p class="mt-2">{{ t.no_images or 'No Images' }}</p>
                </div>
            `;
        } else {
            container.innerHTML = `
                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4" id="${type}Grid">
                    ${typeImages.map(image => createImageCard(image, type)).join('')}
                </div>
            `;
            
            // Setup drag and drop for slider
            if (type === 'slider') {
                setupDragAndDrop(type);
            }
        }
    });
}

// Create image card
function createImageCard(image, type) {
    return `
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden" data-id="${image.id}">
            <div class="aspect-w-16 aspect-h-9">
                <img src="${image.path}" alt="${image.name}" class="w-full h-48 object-cover">
            </div>
            <div class="p-4">
                <h3 class="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">${image.name}</h3>
                <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">${type}</p>
                <div class="mt-3 flex space-x-2">
                    ${type === 'slider' ? `
                        <button onclick="moveImage(${image.id}, 'up')" class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7"></path>
                            </svg>
                        </button>
                        <button onclick="moveImage(${image.id}, 'down')" class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                            </svg>
                        </button>
                    ` : ''}
                    <button onclick="deleteImage(${image.id})" class="text-red-400 hover:text-red-600 dark:hover:text-red-300">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                        </svg>
                    </button>
                </div>
            </div>
        </div>
    `;
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

// Handle file upload
async function handleUpload(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const fileInput = document.getElementById('imageFile');
    
    if (!fileInput.files[0]) {
        showNotification('{{ t.select_file or "Please select a file" }}', 'error');
        return;
    }
    
    try {
        const response = await fetch('/cms/api/images', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('{{ t.image_uploaded or "Image uploaded successfully" }}', 'success');
            fileInput.value = '';
            loadImages(); // Reload images
        } else {
            showNotification(result.message || '{{ t.upload_error or "Upload error" }}', 'error');
        }
    } catch (error) {
        console.error('Upload error:', error);
        showNotification('{{ t.upload_error or "Upload error" }}', 'error');
    }
}

// Delete image
async function deleteImage(imageId) {
    if (!confirm('{{ t.confirm_delete or "Are you sure you want to delete this image?" }}')) {
        return;
    }
    
    try {
        const response = await fetch(`/cms/api/images/${imageId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('{{ t.image_deleted or "Image deleted successfully" }}', 'success');
            loadImages(); // Reload images
        } else {
            showNotification(result.message || '{{ t.delete_error or "Delete error" }}', 'error');
        }
    } catch (error) {
        console.error('Delete error:', error);
        showNotification('{{ t.delete_error or "Delete error" }}', 'error');
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
            showNotification(result.message || '{{ t.move_error or "Move error" }}', 'error');
        }
    } catch (error) {
        console.error('Move error:', error);
        showNotification('{{ t.move_error or "Move error" }}', 'error');
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
            showNotification(result.message || '{{ t.move_error or "Move error" }}', 'error');
        }
    } catch (error) {
        console.error('Move error:', error);
        showNotification('{{ t.move_error or "Move error" }}', 'error');
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
