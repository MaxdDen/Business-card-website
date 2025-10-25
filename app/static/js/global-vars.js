/**
 * Global variables for the application
 * Глобальные переменные приложения
 */

// Server-side variables injection
// Инъекция серверных переменных
function injectServerVariables() {
    // Server-side variables injection
    // Инъекция серверных переменных
    window.defaultLanguage = '{{ default_language }}';
    window.supportedLanguages = {{ supported_languages | tojson | safe }};
    window.currentLanguage = '{{ lang }}';
}

// Initialize global variables from server-side data
// Инициализация глобальных переменных из серверных данных
function initializeGlobalVariables() {
    // These variables should be set by the server in the HTML template
    // Эти переменные должны быть установлены сервером в HTML шаблоне
    
    // Default language (e.g., 'en')
    window.defaultLanguage = window.defaultLanguage || 'en';
    
    // Supported languages array (e.g., ['en', 'ru', 'ua'])
    window.supportedLanguages = window.supportedLanguages || ['en', 'ru', 'ua'];
    
    // Current language (e.g., 'en', 'ru', 'ua')
    window.currentLanguage = window.currentLanguage || 'en';
    
    // Debug logging
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        console.log('Global variables initialized:', {
            defaultLanguage: window.defaultLanguage,
            supportedLanguages: window.supportedLanguages,
            currentLanguage: window.currentLanguage
        });
    }
}

// Initialize when DOM is ready
// Инициализация когда DOM готов
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeGlobalVariables);
} else {
    initializeGlobalVariables();
}
