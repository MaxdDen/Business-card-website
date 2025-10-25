// Template Variables management functionality
document.addEventListener('DOMContentLoaded', async function() {
    // Загружаем переводы
    const t = await window.translations.getTranslations('cms_template_variables', [
        'load_error', 'no_variables', 'sync_loading', 'sync_completed', 'added', 'skipped',
        'sync_error', 'analysis_loading', 'analysis_completed', 'templates', 'variables',
        'analysis_error', 'no_templates', 'problems', 'file', 'unclosed_tag', 'click_refresh_to_load',
        'errors_and_issues', 'no_errors_found', 'click_analyze_to_check'
    ]);
    const syncBtn = document.getElementById('sync-btn');
    const analyzeBtn = document.getElementById('analyze-btn');
    const refreshBtn = document.getElementById('refresh-btn');
    const notifications = document.getElementById('notifications');
    
    // Обработчики кнопок
    syncBtn.addEventListener('click', syncVariables);
    analyzeBtn.addEventListener('click', analyzeTemplates);
    refreshBtn.addEventListener('click', function() {
        loadStatistics();
        clearNotifications();
    });
    
    // Функция показа уведомлений
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `mb-4 p-4 rounded-md ${
            type === 'success' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' :
            type === 'error' ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200' :
            type === 'warning' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200' :
            'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
        }`;
        notification.innerHTML = `
            <div class="flex">
                <div class="flex-shrink-0">
                    <svg class="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path>
                    </svg>
                </div>
                <div class="ml-3">
                    <p class="text-sm font-medium">${message}</p>
                </div>
            </div>
        `;
        notifications.appendChild(notification);
        
        // Автоматически скрываем через 5 секунд
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }
    
    function clearNotifications() {
        notifications.innerHTML = '';
    }
    
    // Загрузка статистики
    async function loadStatistics() {
        try {
            const response = await fetch('/cms/api/template-variables');
            const data = await response.json();
            
            if (data.success) {
                updateStats(data.total_pages, data.total_variables, 0);
            } else {
                console.error('Ошибка загрузки статистики:', data.error);
            }
        } catch (error) {
            console.error('Ошибка загрузки статистики:', error);
        }
    }
    
    // Отображение ошибок
    function displayErrors(errors) {
        const content = document.getElementById('errors-content');
        
        if (!errors || Object.keys(errors).length === 0) {
            content.innerHTML = `
                <div class="text-center py-8">
                    <div class="text-gray-400 dark:text-gray-500 mb-2">
                        <svg class="w-12 h-12 mx-auto" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
                        </svg>
                    </div>
                    <p class="text-gray-500 dark:text-gray-400 font-medium">${t.no_errors_found || 'No errors found'}</p>
                    <p class="text-sm text-gray-400 dark:text-gray-500 mt-1">${t.click_analyze_to_check || 'Click "Analyze Templates" to check for issues'}</p>
                </div>
            `;
            return;
        }
        
        let html = '';
        for (const [page, data] of Object.entries(errors)) {
            const hasIssues = data.has_issues;
            const issueCount = data.syntax_issues.unclosed_tags.length + data.syntax_issues.invalid_syntax.length;
            
            if (hasIssues) {
                html += `
                    <div class="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                        <div class="flex items-center justify-between mb-3">
                            <h4 class="font-medium text-red-900 dark:text-red-100">${page}</h4>
                            <span class="px-2 py-1 text-xs bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200 rounded">
                                ${issueCount} ${t.problems || 'problems'}
                            </span>
                        </div>
                        
                        <div class="space-y-2">
                            <div class="text-sm text-red-700 dark:text-red-300">
                                <strong>${t.file || 'File'}:</strong> ${data.file}
                            </div>
                            
                            ${data.syntax_issues.unclosed_tags.length > 0 ? `
                                <div class="mt-2">
                                    <div class="text-sm font-medium text-red-700 dark:text-red-300 mb-1">${t.unclosed_tag || 'Unclosed tags'}:</div>
                                    <div class="space-y-1">
                                        ${data.syntax_issues.unclosed_tags.map(tag => `
                                            <div class="text-xs text-red-600 dark:text-red-400">• ${tag}</div>
                                        `).join('')}
                                    </div>
                                </div>
                            ` : ''}
                            
                            ${data.syntax_issues.invalid_syntax.length > 0 ? `
                                <div class="mt-2">
                                    <div class="text-sm font-medium text-red-700 dark:text-red-300 mb-1">${t.invalid_syntax || 'Invalid syntax'}:</div>
                                    <div class="space-y-1">
                                        ${data.syntax_issues.invalid_syntax.map(issue => `
                                            <div class="text-xs text-red-600 dark:text-red-400">• ${issue}</div>
                                        `).join('')}
                                    </div>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                `;
            }
        }
        
        if (html === '') {
            content.innerHTML = `
                <div class="text-center py-8">
                    <div class="text-green-400 dark:text-green-500 mb-2">
                        <svg class="w-12 h-12 mx-auto" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
                        </svg>
                    </div>
                    <p class="text-green-600 dark:text-green-400 font-medium">${t.no_errors_found || 'No errors found'}</p>
                    <p class="text-sm text-gray-400 dark:text-gray-500 mt-1">All templates are valid</p>
                </div>
            `;
        } else {
            content.innerHTML = html;
        }
    }
    
    // Синхронизация переменных
    async function syncVariables() {
        syncBtn.disabled = true;
        syncBtn.innerHTML = `<svg class="animate-spin -ml-1 mr-3 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>${t.sync_loading || 'Syncing...'}`;
        
        try {
            const response = await fetch('/cms/api/sync-template-variables', {
                method: 'POST'
            });
            const data = await response.json();
            
            if (data.success) {
                showNotification(`${t.sync_completed || 'Sync completed'}: ${data.results.added_variables} ${t.added || 'added'}, ${data.results.skipped_variables} ${t.skipped || 'skipped'}`, 'success');
                loadDatabaseVariables();
            } else {
                showNotification(t.sync_error || 'Sync error', 'error');
            }
        } catch (error) {
            console.error('Ошибка синхронизации:', error);
            showNotification(t.sync_error || 'Sync error', 'error');
        } finally {
            syncBtn.disabled = false;
            syncBtn.innerHTML = '<svg class="w-4 h-4 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>Sync Variables';
        }
    }
    
    // Анализ шаблонов
    async function analyzeTemplates() {
        const content = document.getElementById('errors-content');
        
        analyzeBtn.disabled = true;
        analyzeBtn.innerHTML = `<svg class="animate-spin -ml-1 mr-3 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>${t.analysis_loading || 'Analyzing...'}`;
        
        // Показываем индикатор загрузки в блоке ошибок
        content.innerHTML = `
            <div class="text-center py-8">
                <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                <p class="mt-2 text-gray-500 dark:text-gray-400">${t.analysis_loading || 'Analyzing templates...'}</p>
            </div>
        `;
        
        try {
            const response = await fetch('/cms/api/template-analysis');
            const data = await response.json();
            
            if (data.success) {
                displayErrors(data.analysis);
                showNotification(`${t.analysis_completed || 'Analysis completed'}: ${data.total_templates} ${t.templates || 'templates'}, ${data.total_variables} ${t.variables || 'variables'}`, 'success');
            } else {
                // Показываем ошибку в блоке ошибок
                content.innerHTML = `
                    <div class="text-center py-8">
                        <div class="text-red-600 dark:text-red-400 mb-2">
                            <svg class="w-12 h-12 mx-auto" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
                            </svg>
                        </div>
                        <p class="text-red-600 dark:text-red-400 font-medium">${t.analysis_error || 'Analysis failed'}</p>
                        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Please try again or check server logs</p>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Ошибка анализа:', error);
            content.innerHTML = `
                <div class="text-center py-8">
                    <div class="text-red-600 dark:text-red-400 mb-2">
                        <svg class="w-12 h-12 mx-auto" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
                        </svg>
                    </div>
                    <p class="text-red-600 dark:text-red-400 font-medium">${t.analysis_error || 'Analysis failed'}</p>
                    <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Network error or server unavailable</p>
                </div>
            `;
        } finally {
            analyzeBtn.disabled = false;
            analyzeBtn.innerHTML = '<svg class="w-4 h-4 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path></svg>Analyze Templates';
        }
    }
    
    
    // Обновление статистики
    function updateStats(pages, variables, missing) {
        document.getElementById('total-pages').textContent = pages;
        document.getElementById('total-variables').textContent = variables;
        document.getElementById('missing-variables').textContent = missing;
    }
});
