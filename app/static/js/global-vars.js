/*
 * Global variables for the application
 * Глобальные переменные приложения
 */

// Глобальные переменные
let supportedLanguages = ['en']; // Fallback - массив кодов
let languagesInfo = {'en': {code: 'en', name: 'EN', full_name: 'English'}}; // Fallback - объект с информацией
let defaultLanguage = 'en'; // Fallback
let currentLanguage = 'en'; // Fallback

/*
 * Загрузить поддерживаемые языки через API
 * @returns {Promise<Object>} Объект с информацией о языках
 */
async function loadSupportedLanguages() {
    try {
        const response = await fetch('/api/supported-languages');
        
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                supportedLanguages = data.languages;
                languagesInfo = data.languages_info;
                defaultLanguage = data.default_language;
                
                // Определяем текущий язык из URL
                currentLanguage = getCurrentLanguageFromUrl();
                
                return languagesInfo;
            }
        }
    } catch (error) {
        console.error('Error loading supported languages:', error);
    }
    
    // Fallback значения
    currentLanguage = getCurrentLanguageFromUrl();
    return languagesInfo;
}

/*
 * Получить текущий язык из URL
 * @returns {string} Код языка
 */
function getCurrentLanguageFromUrl() {
    const path = window.location.pathname;
    const langMatch = path.match(/^\/([a-z]{2})(?:\/|$)/);
    return langMatch ? langMatch[1] : defaultLanguage;
}

/*
 * Получить названия языков (короткие коды)
 * @returns {Object} Объект с маппингом кодов на названия
 */
function getLanguageNames() {
    const names = {};
    Object.keys(languagesInfo).forEach(lang => {
        names[lang] = languagesInfo[lang].name;
    });
    return names;
}

/*
 * Получить полные названия языков
 * @returns {Object} Объект с маппингом кодов на полные названия
 */
function getLanguageFullNames() {
    const fullNames = {};
    Object.keys(languagesInfo).forEach(lang => {
        fullNames[lang] = languagesInfo[lang].full_name;
    });
    return fullNames;
}

/*
 * Инициализация глобальных переменных
 */
async function initializeGlobalVariables() {
    await loadSupportedLanguages();
    
    // Делаем переменные доступными глобально
    window.supportedLanguages = supportedLanguages;
    window.languagesInfo = languagesInfo;
    window.defaultLanguage = defaultLanguage;
    window.currentLanguage = currentLanguage;
    
    // Вызываем событие для уведомления других скриптов
    window.dispatchEvent(new CustomEvent('globalVariablesLoaded', {
        detail: {
            supportedLanguages,
            languagesInfo,
            defaultLanguage,
            currentLanguage
        }
    }));
}

// Инициализация при загрузке DOM
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeGlobalVariables);
} else {
    initializeGlobalVariables();
}

// Экспортируем функции для использования в других скриптах
window.loadSupportedLanguages = loadSupportedLanguages;
window.getCurrentLanguageFromUrl = getCurrentLanguageFromUrl;
window.getLanguageNames = getLanguageNames;
window.getLanguageFullNames = getLanguageFullNames;