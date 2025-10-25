/**
 * Translation management utility
 * Утилита для работы с переводами
 */

class TranslationManager {
    constructor() {
        this.cache = new Map();
        this.currentLang = window.currentLanguage || 'en';
    }

    /**
     * Load translations for a module
     * Загрузить переводы для модуля
     */
    async loadTranslations(module) {
        // Проверяем кэш
        const cacheKey = `${module}_${this.currentLang}`;
        if (this.cache.has(cacheKey)) {
            return this.cache.get(cacheKey);
        }

        try {
            const response = await fetch(`/cms/api/translations?module=${module}&lang=${this.currentLang}`);
            const data = await response.json();
            
            if (data.success) {
                this.cache.set(cacheKey, data.translations);
                return data.translations;
            } else {
                console.error('Ошибка загрузки переводов:', data.message);
                return {};
            }
        } catch (error) {
            console.error('Ошибка загрузки переводов:', error);
            return {};
        }
    }

    /**
     * Get translation by key
     * Получить перевод по ключу
     */
    async t(module, key, fallback = '') {
        const translations = await this.loadTranslations(module);
        return translations[key] || fallback;
    }

    /**
     * Get multiple translations
     * Получить несколько переводов
     */
    async getTranslations(module, keys) {
        const translations = await this.loadTranslations(module);
        const result = {};
        
        for (const key of keys) {
            result[key] = translations[key] || '';
        }
        
        return result;
    }

    /**
     * Clear cache for a module
     * Очистить кэш для модуля
     */
    clearCache(module = null) {
        if (module) {
            const cacheKey = `${module}_${this.currentLang}`;
            this.cache.delete(cacheKey);
        } else {
            this.cache.clear();
        }
    }
}

// Создаем глобальный экземпляр
window.translations = new TranslationManager();
