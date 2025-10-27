// Global translations system for JavaScript modules
// Prevent duplicate class declaration
if (typeof window.TranslationManager !== 'undefined') {
    console.warn('⚠️ TranslationManager already exists, skipping redefinition');
} else {
    class TranslationManager {
    constructor() {
        this.translations = {};
        this.currentLang = this.getCurrentLanguage();
        this.loadTranslations();
    }

    // Get current language from URL or default to 'en'
    getCurrentLanguage() {
        const path = window.location.pathname;
        const langMatch = path.match(/\/cms\/([a-z]{2})\//);
        return langMatch ? langMatch[1] : 'en';
    }

    // Load translations from API
    async loadTranslations() {
        try {
            // Check if we're on a CMS page (authenticated)
            const isCmsPage = window.location.pathname.includes('/cms/');
            
            if (isCmsPage) {
                // Load translations for CMS modules
                const modules = ['cms_texts', 'cms_images', 'cms_seo', 'cms_users', 'cms_template_variables'];
                const promises = modules.map(module => 
                    fetch(`/cms/api/translations?module=${module}&lang=${this.currentLang}`, {
                        credentials: 'include'
                    }).then(response => {
                        if (response.status === 401) {
                            console.warn(`⚠️ Not authenticated for module: ${module}`);
                            return { success: false, module };
                        }
                        return response.json();
                    })
                );
                
                const results = await Promise.all(promises);
                
                // Combine all translations
                this.translations = {};
                for (const result of results) {
                    if (result.success && result.translations) {
                        this.translations[result.module] = result.translations;
                    }
                }
                
            } else {
                // For public pages, load only header translations
                try {
                    const response = await fetch(`/api/translations?module=header&lang=${this.currentLang}`, {
                        credentials: 'include'
                    });
                    
                    if (response.ok) {
                        const data = await response.json();
                        if (data.success && data.translations) {
                            this.translations.header = data.translations;
                            console.log('✅ Public translations loaded');
                        }
                    }
                } catch (error) {
                    console.warn('⚠️ Could not load public translations:', error);
                }
            }
            
        } catch (error) {
            console.error('💥 Error loading translations:', error);
        }
    }

    // Get translation by key with fallback
    t(key, fallback = null) {
        const keys = key.split('.');
        let value = this.translations;
        
        for (const k of keys) {
            if (value && typeof value === 'object' && k in value) {
                value = value[k];
            } else {
                return fallback || key;
            }
        }
        
        return value || fallback || key;
    }

    // Get translations for specific module
    getModuleTranslations(moduleName) {
        return this.translations[moduleName] || {};
    }

    // Get translations for specific module and keys (for compatibility)
    async getTranslations(moduleName, keys = []) {
        // Ensure translations are loaded
        if (Object.keys(this.translations).length === 0) {
            await this.loadTranslations();
        }
        
        const moduleTranslations = this.getModuleTranslations(moduleName);
        
        if (keys.length === 0) {
            return moduleTranslations;
        }
        
        // Return only requested keys
        const result = {};
        for (const key of keys) {
            result[key] = moduleTranslations[key] || key;
        }
        
        return result;
    }
}

// Global translation manager instance
window.translationManager = new TranslationManager();

// Export translations object for compatibility
window.translations = {
    getTranslations: (moduleName, keys = []) => window.translationManager.getTranslations(moduleName, keys)
};

// Convenience function for translations
window.t = (key, fallback = null) => window.translationManager.t(key, fallback);

// Module-specific translation functions
window.getTextsTranslations = () => window.translationManager.getModuleTranslations('texts');
window.getTemplateVariablesTranslations = () => window.translationManager.getModuleTranslations('template_variables');
window.getSessionMonitorTranslations = () => window.translationManager.getModuleTranslations('session_monitor');
window.getSeoTranslations = () => window.translationManager.getModuleTranslations('seo');
window.getImagesTranslations = () => window.translationManager.getModuleTranslations('images');

} // End of else block for duplicate prevention