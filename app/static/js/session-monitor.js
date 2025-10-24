/**
 * Session Monitor - отслеживание истечения сессии на клиенте
 * Автоматическая переадресация на страницу логина при истечении JWT токена
 */

class SessionMonitor {
    constructor() {
        this.checkInterval = null;
        this.checkIntervalMs = 60000; // Проверяем каждую минуту
        this.warningTimeMs = 300000; // Предупреждение за 5 минут до истечения
        this.isWarningShown = false;
        this.warningModal = null;
        
        this.init();
    }
    
    init() {
        // Запускаем мониторинг только на CMS страницах
        if (this.isCMSPage()) {
            this.startMonitoring();
            this.setupVisibilityChangeHandler();
        }
    }
    
    isCMSPage() {
        return window.location.pathname.startsWith('/cms') || 
               window.location.pathname.includes('/cms');
    }
    
    startMonitoring() {
        // Проверяем сразу при загрузке
        this.checkSession();
        
        // Устанавливаем периодическую проверку
        this.checkInterval = setInterval(() => {
            this.checkSession();
        }, this.checkIntervalMs);
    }
    
    stopMonitoring() {
        if (this.checkInterval) {
            clearInterval(this.checkInterval);
            this.checkInterval = null;
        }
    }
    
    async checkSession() {
        try {
            // Проверяем сессию через API endpoint
            const response = await fetch('/cms/api/session-check', {
                method: 'GET',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.status === 401) {
                // Сессия истекла, перенаправляем на логин
                this.redirectToLogin();
                return;
            }
            
            if (response.ok) {
                const data = await response.json();
                this.handleSessionData(data);
            }
            
        } catch (error) {
            console.error('Session check failed:', error);
            // При ошибке сети тоже перенаправляем на логин
            this.redirectToLogin();
        }
    }
    
    handleSessionData(data) {
        if (data.expires_at) {
            const expiresAt = new Date(data.expires_at);
            const now = new Date();
            const timeUntilExpiry = expiresAt.getTime() - now.getTime();
            
            // Если сессия истекает в ближайшие 5 минут, показываем предупреждение
            if (timeUntilExpiry <= this.warningTimeMs && timeUntilExpiry > 0 && !this.isWarningShown) {
                this.showExpiryWarning(timeUntilExpiry);
            }
            
            // Если сессия уже истекла, перенаправляем
            if (timeUntilExpiry <= 0) {
                this.redirectToLogin();
            }
        }
    }
    
    showExpiryWarning(timeUntilExpiry) {
        this.isWarningShown = true;
        
        // Создаем модальное окно с предупреждением
        this.warningModal = this.createWarningModal(timeUntilExpiry);
        document.body.appendChild(this.warningModal);
        
        // Автоматически скрываем через 10 секунд
        setTimeout(() => {
            this.hideExpiryWarning();
        }, 10000);
    }
    
    createWarningModal(timeUntilExpiry) {
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        modal.innerHTML = `
            <div class="bg-white dark:bg-gray-900 rounded-lg p-6 max-w-md mx-4 shadow-xl">
                <div class="flex items-center mb-4">
                    <div class="flex-shrink-0">
                        <svg class="h-6 w-6 text-yellow-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                        </svg>
                    </div>
                    <div class="ml-3">
                        <h3 class="text-lg font-medium text-gray-900 dark:text-gray-100">
                            Сессия скоро истечет
                        </h3>
                    </div>
                </div>
                <div class="mb-4">
                    <p class="text-sm text-gray-600 dark:text-gray-400">
                        Ваша сессия истечет через ${Math.ceil(timeUntilExpiry / 60000)} минут. 
                        Пожалуйста, сохраните ваши изменения.
                    </p>
                </div>
                <div class="flex justify-end space-x-3">
                    <button type="button" class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600" onclick="sessionMonitor.hideExpiryWarning()">
                        Понятно
                    </button>
                    <button type="button" class="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700" onclick="sessionMonitor.refreshSession()">
                        Продлить сессию
                    </button>
                </div>
            </div>
        `;
        return modal;
    }
    
    hideExpiryWarning() {
        if (this.warningModal) {
            this.warningModal.remove();
            this.warningModal = null;
        }
    }
    
    async refreshSession() {
        try {
            const response = await fetch('/cms/api/session-refresh', {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                this.hideExpiryWarning();
                this.isWarningShown = false;
                // Показываем уведомление об успехе
                this.showSuccessMessage('Сессия продлена');
            } else {
                this.redirectToLogin();
            }
        } catch (error) {
            console.error('Session refresh failed:', error);
            this.redirectToLogin();
        }
    }
    
    showSuccessMessage(message) {
        // Создаем временное уведомление об успехе
        const notification = document.createElement('div');
        notification.className = 'fixed top-4 right-4 bg-green-500 text-white px-4 py-2 rounded-md shadow-lg z-50';
        notification.textContent = message;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
    
    redirectToLogin() {
        this.stopMonitoring();
        
        // Получаем текущий URL для редиректа после логина
        const currentPath = window.location.pathname;
        const loginUrl = `/login?next=${encodeURIComponent(currentPath)}`;
        
        // Показываем уведомление о перенаправлении
        const notification = document.createElement('div');
        notification.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        notification.innerHTML = `
            <div class="bg-white dark:bg-gray-900 rounded-lg p-6 max-w-md mx-4 shadow-xl text-center">
                <div class="mb-4">
                    <svg class="h-12 w-12 text-blue-500 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                </div>
                <h3 class="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
                    Сессия истекла
                </h3>
                <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">
                    Вы будете перенаправлены на страницу входа...
                </p>
                <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500 mx-auto"></div>
            </div>
        `;
        document.body.appendChild(notification);
        
        // Перенаправляем через 2 секунды
        setTimeout(() => {
            window.location.href = loginUrl;
        }, 2000);
    }
    
    setupVisibilityChangeHandler() {
        // Проверяем сессию при возвращении на вкладку
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.checkSession();
            }
        });
    }
}

// Инициализируем мониторинг сессии
const sessionMonitor = new SessionMonitor();

// Экспортируем для использования в других скриптах
window.sessionMonitor = sessionMonitor;
