/**
 * Language switching functionality with cookie persistence
 * Поддержка переключения языков с сохранением в cookies
 */

/**
 * Set language preference in cookie and redirect
 * Установить предпочтение языка в cookie и перенаправить
 */
function switchLanguage(language) {
    try {
        // Use API endpoint to set language cookie
        fetch('/api/set-language', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `language=${language}`
        })
        .then(response => {
            if (response.ok) {
                // Get current path and clean it from language prefix
                const currentPath = window.location.pathname;
                const cleanPath = getCleanPath(currentPath);
                
                // Generate new URL with selected language
                let newUrl;
                const defaultLanguage = window.defaultLanguage || 'en';
                if (language === defaultLanguage) {
                    // Для дефолтного языка не добавляем префикс
                    newUrl = cleanPath;
                } else {
                    // Для других языков добавляем префикс
                    newUrl = `/${language}${cleanPath}`;
                }
                
                // Redirect to new URL
                window.location.href = newUrl;
            } else {
                console.error('Failed to set language:', response.status);
                // Fallback: set cookie manually and redirect
                document.cookie = `user_language=${language}; max-age=${365*24*60*60}; path=/; samesite=lax`;
                const defaultLanguage = window.defaultLanguage || 'en';
                if (language === defaultLanguage) {
                    window.location.href = '/';
                } else {
                    window.location.href = `/${language}/`;
                }
            }
        })
        .catch(error => {
            console.error('Error switching language:', error);
            // Fallback: set cookie manually and redirect
            document.cookie = `user_language=${language}; max-age=${365*24*60*60}; path=/; samesite=lax`;
            const defaultLanguage = window.defaultLanguage || 'en';
            if (language === defaultLanguage) {
                window.location.href = '/';
            } else {
                window.location.href = `/${language}/`;
            }
        });
        
    } catch (error) {
        console.error('Error switching language:', error);
        // Fallback: just redirect to language root
        const defaultLanguage = window.defaultLanguage || 'en';
        if (language === defaultLanguage) {
            window.location.href = '/';
        } else {
            window.location.href = `/${language}/`;
        }
    }
}

/**
 * Get clean path without language prefix
 * Получить чистый путь без языкового префикса
 */
function getCleanPath(path) {
    const supportedLanguages = window.supportedLanguages || ['en', 'ru', 'ua'];
    const defaultLanguage = window.defaultLanguage || 'en';
    
    // Debug logging
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        console.log('getCleanPath input:', path);
        console.log('supportedLanguages:', supportedLanguages);
        console.log('defaultLanguage:', defaultLanguage);
    }
    
    // Исключаем дефолтный язык из проверки
    const nonDefaultLanguages = supportedLanguages.filter(lang => lang !== defaultLanguage);
    
    for (const lang of nonDefaultLanguages) {
        if (path.startsWith(`/${lang}/`)) {
            const cleanPath = path.substring(`/${lang}`.length);
            console.log(`Removed ${lang} prefix:`, path, '->', cleanPath);
            return cleanPath;
        } else if (path === `/${lang}`) {
            console.log(`Removed ${lang} prefix:`, path, '->', '/');
            return '/';
        }
    }
    
    console.log('No language prefix found, returning original path:', path);
    return path;
}

/**
 * Initialize language switcher
 * Инициализация переключателя языков
 */
function initLanguageSwitcher() {
    // Add click handlers to language links
    const languageLinks = document.querySelectorAll('[data-language-switch]');
    
    languageLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const language = this.getAttribute('data-language-switch');
            switchLanguage(language);
        });
    });
    
    // Add click handlers to language buttons
    const languageButtons = document.querySelectorAll('[data-language-button]');
    
    languageButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const language = this.getAttribute('data-language-button');
            switchLanguage(language);
        });
    });
}

/**
 * Get current language from URL or cookie
 * Получить текущий язык из URL или cookie
 */
function getCurrentLanguage() {
    // First try to get from URL
    const path = window.location.pathname;
    const match = path.match(/^\/([a-z]{2})(?:\/|$)/);
    if (match) {
        return match[1];
    }
    
    // Fallback to cookie
    const cookies = document.cookie.split(';');
    for (const cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'user_language') {
            return value;
        }
    }
    
    return 'en'; // Default language
}

/**
 * Highlight current language in switcher
 * Выделить текущий язык в переключателе
 */
function highlightCurrentLanguage() {
    const currentLang = getCurrentLanguage();
    const languageElements = document.querySelectorAll('[data-language-switch], [data-language-button]');
    
    languageElements.forEach(element => {
        const elementLang = element.getAttribute('data-language-switch') || 
                          element.getAttribute('data-language-button');
        
        if (elementLang === currentLang) {
            element.classList.add('active', 'bg-blue-600', 'text-white');
            element.classList.remove('text-gray-600', 'dark:text-gray-400');
        } else {
            element.classList.remove('active', 'bg-blue-600', 'text-white');
            element.classList.add('text-gray-600', 'dark:text-gray-400');
        }
    });
}

/**
 * Initialize on DOM ready
 * Инициализация при готовности DOM
 */
document.addEventListener('DOMContentLoaded', function() {
    initLanguageSwitcher();
    highlightCurrentLanguage();
});

// Export functions for global use
window.switchLanguage = switchLanguage;
window.getCurrentLanguage = getCurrentLanguage;
