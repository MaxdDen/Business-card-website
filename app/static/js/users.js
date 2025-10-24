// Users management functionality
document.addEventListener('DOMContentLoaded', function() {
    // Загружаем пользователей при загрузке страницы
    loadUsers();
    
    // Обработчики для модальных окон
    const addUserBtn = document.getElementById('addUserBtn');
    const addUserModal = document.getElementById('addUserModal');
    const cancelAddUser = document.getElementById('cancelAddUser');
    const addUserForm = document.getElementById('addUserForm');
    
    const resetPasswordModal = document.getElementById('resetPasswordModal');
    const cancelResetPassword = document.getElementById('cancelResetPassword');
    const resetPasswordForm = document.getElementById('resetPasswordForm');
    
    // Показать модальное окно добавления пользователя
    addUserBtn.addEventListener('click', function() {
        addUserModal.classList.remove('hidden');
    });
    
    // Скрыть модальное окно добавления пользователя
    cancelAddUser.addEventListener('click', function() {
        addUserModal.classList.add('hidden');
        addUserForm.reset();
    });
    
    // Скрыть модальное окно сброса пароля
    cancelResetPassword.addEventListener('click', function() {
        resetPasswordModal.classList.add('hidden');
        resetPasswordForm.reset();
    });
    
    // Закрытие модальных окон по клику вне их
    addUserModal.addEventListener('click', function(e) {
        if (e.target === addUserModal) {
            addUserModal.classList.add('hidden');
            addUserForm.reset();
        }
    });
    
    resetPasswordModal.addEventListener('click', function(e) {
        if (e.target === resetPasswordModal) {
            resetPasswordModal.classList.add('hidden');
            resetPasswordForm.reset();
        }
    });
    
    // Обработка формы добавления пользователя
    addUserForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(addUserForm);
        
        try {
            const response = await fetch('/cms/api/users', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                showNotification('{{ t.user_created or "User created successfully" }}', 'success');
                addUserModal.classList.add('hidden');
                addUserForm.reset();
                loadUsers(); // Перезагружаем список пользователей
            } else {
                showNotification(result.message || '{{ t.create_error or "Error creating user" }}', 'error');
            }
        } catch (error) {
            console.error('Ошибка:', error);
            showNotification('{{ t.create_error or "Error creating user" }}', 'error');
        }
    });
    
    // Обработка формы сброса пароля
    resetPasswordForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const userId = document.getElementById('resetUserId').value;
        const formData = new FormData(resetPasswordForm);
        
        try {
            const response = await fetch(`/cms/api/users/${userId}/reset-password`, {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                showNotification('{{ t.password_reset or "Password reset successfully" }}', 'success');
                resetPasswordModal.classList.add('hidden');
                resetPasswordForm.reset();
            } else {
                showNotification(result.message || '{{ t.reset_error or "Error resetting password" }}', 'error');
            }
        } catch (error) {
            console.error('Ошибка:', error);
            showNotification('{{ t.reset_error or "Error resetting password" }}', 'error');
        }
    });
});

// Загрузить список пользователей
async function loadUsers() {
    try {
        const response = await fetch('/cms/api/users');
        const data = await response.json();
        
        if (data.success) {
            renderUsers(data.users);
        } else {
            showNotification('{{ t.load_error or "Load error" }}: ' + data.message, 'error');
        }
    } catch (error) {
        console.error('Ошибка загрузки пользователей:', error);
        showNotification('{{ t.load_error or "Load error" }}', 'error');
    }
}

// Отобразить список пользователей
function renderUsers(users) {
    const tbody = document.getElementById('usersTableBody');
    tbody.innerHTML = '';
    
    users.forEach(user => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-gray-100">
                ${user.email}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                ${user.role}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                ${new Date(user.created_at).toLocaleDateString()}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                <button onclick="resetPassword(${user.id})" class="text-indigo-600 hover:text-indigo-900 dark:text-indigo-400 dark:hover:text-indigo-300 mr-4">
                    {{ t.reset_password or "Reset Password" }}
                </button>
                <button onclick="deleteUser(${user.id})" class="text-red-600 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300">
                    {{ t.delete or "Delete" }}
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// Сброс пароля пользователя
function resetPassword(userId) {
    document.getElementById('resetUserId').value = userId;
    document.getElementById('resetPasswordModal').classList.remove('hidden');
}

// Удаление пользователя
async function deleteUser(userId) {
    if (!confirm('{{ t.confirm_delete or "Are you sure you want to delete this user?" }}')) {
        return;
    }
    
    try {
        const response = await fetch(`/cms/api/users/${userId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('{{ t.user_deleted or "User deleted successfully" }}', 'success');
            loadUsers(); // Перезагружаем список пользователей
        } else {
            showNotification(result.message || '{{ t.delete_error or "Error deleting user" }}', 'error');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        showNotification('{{ t.delete_error or "Error deleting user" }}', 'error');
    }
}

// Показать уведомление
function showNotification(message, type) {
    const notification = document.getElementById('notification');
    notification.className = `mt-4 p-4 rounded-md ${type === 'success' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'}`;
    notification.textContent = message;
    notification.classList.remove('hidden');
    
    setTimeout(() => {
        notification.classList.add('hidden');
    }, 5000);
}
