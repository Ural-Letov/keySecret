// Основные JavaScript функции для веб-приложения

// Утилиты для работы с буфером обмена
function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
        return navigator.clipboard.writeText(text);
    } else {
        // Fallback для старых браузеров
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        return new Promise((resolve, reject) => {
            document.execCommand('copy') ? resolve() : reject();
            textArea.remove();
        });
    }
}

// Показать уведомление
function showNotification(message, type = 'info') {
    // Создаем элемент уведомления
    const notification = document.createElement('div');
    notification.className = `alert alert-${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
        ${message}
    `;
    
    // Добавляем в контейнер сообщений
    let messagesContainer = document.querySelector('.messages');
    if (!messagesContainer) {
        messagesContainer = document.createElement('div');
        messagesContainer.className = 'messages';
        document.querySelector('.container').insertBefore(messagesContainer, document.querySelector('.main-content'));
    }
    
    messagesContainer.appendChild(notification);
    
    // Автоматически удаляем через 5 секунд
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 5000);
}

// Обработка форм с AJAX
function handleFormSubmit(form, successCallback, errorCallback) {
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(form);
        const url = form.action || window.location.href;
        
        fetch(url, {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (response.ok) {
                return response.text();
            }
            throw new Error('Network response was not ok');
        })
        .then(data => {
            if (successCallback) successCallback(data);
        })
        .catch(error => {
            if (errorCallback) errorCallback(error);
        });
    });
}

// Анимации загрузки
function showLoading(element, text = 'Загрузка...') {
    element.innerHTML = `
        <div class="loading">
            <i class="fas fa-spinner fa-spin"></i>
            <span>${text}</span>
        </div>
    `;
}

function hideLoading(element) {
    const loading = element.querySelector('.loading');
    if (loading) {
        loading.remove();
    }
}

// Валидация форм
function validateForm(form) {
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.style.borderColor = 'var(--error-color)';
            isValid = false;
        } else {
            field.style.borderColor = '';
        }
    });
    
    return isValid;
}

// Очистка стилей валидации
function clearValidationStyles(form) {
    const fields = form.querySelectorAll('input, textarea, select');
    fields.forEach(field => {
        field.style.borderColor = '';
    });
}

// Обработка ошибок API
function handleApiError(error) {
    console.error('API Error:', error);
    showNotification('Произошла ошибка при выполнении запроса', 'error');
}

// Утилиты для работы с паролями
function togglePasswordVisibility(button) {
    const passwordField = button.closest('.password-field');
    const passwordText = passwordField.querySelector('.password-text');
    const icon = button.querySelector('i');
    const password = passwordField.dataset.password;
    
    if (passwordText.textContent === '••••••••') {
        passwordText.textContent = password;
        icon.className = 'fas fa-eye-slash';
    } else {
        passwordText.textContent = '••••••••';
        icon.className = 'fas fa-eye';
    }
}

function copyPassword(password) {
    copyToClipboard(password)
        .then(() => {
            showNotification('📋 Пароль скопирован в буфер обмена!', 'success');
        })
        .catch(() => {
            showNotification('❌ Ошибка при копировании пароля', 'error');
        });
}

// Утилиты для работы с ключами
function copyMasterKey(key) {
    copyToClipboard(key)
        .then(() => {
            showNotification('📋 Мастер-ключ скопирован в буфер обмена!', 'success');
        })
        .catch(() => {
            showNotification('❌ Ошибка при копировании ключа', 'error');
        });
}

function copySharedKey(key) {
    copyToClipboard(key)
        .then(() => {
            showNotification('📋 Ключ скопирован в буфер обмена!', 'success');
        })
        .catch(() => {
            showNotification('❌ Ошибка при копировании ключа', 'error');
        });
}

// Автоматическое скрытие уведомлений
document.addEventListener('DOMContentLoaded', function() {
    // Автоматически скрываем уведомления через 5 секунд
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (alert.parentNode) {
                alert.style.opacity = '0';
                setTimeout(() => {
                    if (alert.parentNode) {
                        alert.parentNode.removeChild(alert);
                    }
                }, 300);
            }
        }, 5000);
    });
    
    // Очищаем стили валидации при вводе
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            input.addEventListener('input', function() {
                this.style.borderColor = '';
            });
        });
    });
});

// Экспорт функций для глобального использования
window.copyToClipboard = copyToClipboard;
window.showNotification = showNotification;
window.handleFormSubmit = handleFormSubmit;
window.showLoading = showLoading;
window.hideLoading = hideLoading;
window.validateForm = validateForm;
window.clearValidationStyles = clearValidationStyles;
window.handleApiError = handleApiError;
window.togglePasswordVisibility = togglePasswordVisibility;
window.copyPassword = copyPassword;
window.copyMasterKey = copyMasterKey;
window.copySharedKey = copySharedKey;
