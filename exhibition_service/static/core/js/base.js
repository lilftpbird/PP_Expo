// exhibition_service/static/core/js/base.js
// Основной JavaScript файл для базового шаблона

$(document).ready(function() {
    // ===========================================
    // НАВИГАЦИЯ И МЕНЮ
    // ===========================================
    
    // Обработка мобильного меню
    $('.navbar-toggler').click(function(e) {
        e.preventDefault();
        e.stopPropagation();
        $('#navbarNav').toggleClass('show');
        $('body').toggleClass('menu-open');
        
        // Анимация иконки гамбургера
        $(this).toggleClass('active');
    });
    
    // Закрытие меню при клике вне его
    $(document).on('click', function(e) {
        if (!$(e.target).closest('.navbar-collapse').length && 
            !$(e.target).closest('.navbar-toggler').length && 
            $('#navbarNav').hasClass('show')) {
            $('#navbarNav').removeClass('show');
            $('body').removeClass('menu-open');
            $('.navbar-toggler').removeClass('active');
        }
    });
    
    // Обработка выпадающих меню
    $('.dropdown-toggle').click(function(e) {
        // На мобильных устройствах предотвращаем стандартное поведение
        if (window.innerWidth < 992) {
            e.preventDefault();
            $(this).next('.dropdown-menu').toggleClass('show');
        }
    });
    
    // Улучшенная обработка dropdown для десктопа
    $('.dropdown').hover(
        function() {
            if (window.innerWidth >= 992) {
                $(this).addClass('show');
                $(this).find('.dropdown-menu').addClass('show');
            }
        },
        function() {
            if (window.innerWidth >= 992) {
                $(this).removeClass('show');
                $(this).find('.dropdown-menu').removeClass('show');
            }
        }
    );
    
    // Закрытие всех dropdown при клике вне их
    $(document).on('click', function(e) {
        if (!$(e.target).closest('.dropdown').length) {
            $('.dropdown').removeClass('show');
            $('.dropdown-menu').removeClass('show');
        }
    });
    
    // ===========================================
    // ПОИСК
    // ===========================================
    
    // Переключение формы поиска
    window.toggleSearch = function() {
        $('.search-form').toggleClass('active');
        if ($('.search-form').hasClass('active')) {
            setTimeout(function() {
                $('.search-form input').focus();
            }, 300);
        }
    };
    
    // Закрытие поиска при клике вне его
    $(document).on('click', function(e) {
        if (!$(e.target).closest('.search-container').length) {
            $('.search-form').removeClass('active');
        }
    });
    
    // Автозаполнение поиска
    const searchInput = document.querySelector('input[type="search"]');
    if (searchInput) {
        let autocompleteResults = document.querySelector('.autocomplete-results');
        
        // Создаем контейнер для результатов если его нет
        if (!autocompleteResults) {
            autocompleteResults = document.createElement('div');
            autocompleteResults.className = 'autocomplete-results';
            searchInput.parentNode.appendChild(autocompleteResults);
        }
        
        let searchTimeout;
        
        searchInput.addEventListener('input', function() {
            const query = this.value.trim();
            
            // Очищаем предыдущий таймаут
            clearTimeout(searchTimeout);
            
            if (query.length < 2) {
                autocompleteResults.innerHTML = '';
                autocompleteResults.style.display = 'none';
                return;
            }
            
            // Задержка для уменьшения количества запросов
            searchTimeout = setTimeout(() => {
                performSearch(query, autocompleteResults);
            }, 300);
        });
        
        // Скрываем автозаполнение при клике вне его
        document.addEventListener('click', function(e) {
            if (e.target !== searchInput && !autocompleteResults.contains(e.target)) {
                autocompleteResults.style.display = 'none';
            }
        });
        
        // Обработка клавиш в поиске
        searchInput.addEventListener('keydown', function(e) {
            const items = autocompleteResults.querySelectorAll('.autocomplete-item');
            const activeItem = autocompleteResults.querySelector('.autocomplete-item.active');
            
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                if (activeItem) {
                    activeItem.classList.remove('active');
                    const next = activeItem.nextElementSibling || items[0];
                    next.classList.add('active');
                } else if (items.length > 0) {
                    items[0].classList.add('active');
                }
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                if (activeItem) {
                    activeItem.classList.remove('active');
                    const prev = activeItem.previousElementSibling || items[items.length - 1];
                    prev.classList.add('active');
                }
            } else if (e.key === 'Enter') {
                e.preventDefault();
                if (activeItem) {
                    activeItem.click();
                } else {
                    // Выполняем поиск
                    this.closest('form').submit();
                }
            } else if (e.key === 'Escape') {
                autocompleteResults.style.display = 'none';
                this.blur();
            }
        });
    }
    
    // ===========================================
    // ИЗМЕНЕНИЕ СТИЛЯ НАВБАРА ПРИ ПРОКРУТКЕ
    // ===========================================
    
    let lastScrollTop = 0;
    $(window).scroll(function() {
        const scrollTop = $(this).scrollTop();
        const navbar = $('.navbar');
        
        // Изменение стиля при прокрутке
        if (scrollTop > 50) {
            navbar.addClass('scrolled').css({
                'padding': '8px 0',
                'background-color': 'rgba(33, 33, 33, 0.95)',
                'backdrop-filter': 'blur(10px)'
            });
        } else {
            navbar.removeClass('scrolled').css({
                'padding': '15px 0',
                'background-color': '#212121',
                'backdrop-filter': 'none'
            });
        }
        
        // Скрытие/показ навбара при прокрутке (опционально)
        if (scrollTop > lastScrollTop && scrollTop > 100) {
            // Прокрутка вниз - скрываем навбар
            navbar.css('transform', 'translateY(-100%)');
        } else {
            // Прокрутка вверх - показываем навбар
            navbar.css('transform', 'translateY(0)');
        }
        
        lastScrollTop = scrollTop;
    });
    
    // ===========================================
    // ОБРАБОТКА СООБЩЕНИЙ
    // ===========================================
    
    // Автоматическое скрытие сообщений
    $('.alert').each(function() {
        const alert = $(this);
        if (!alert.hasClass('alert-permanent')) {
            // Добавляем прогресс-бар
            alert.append('<div class="alert-progress"></div>');
            
            setTimeout(function() {
                alert.fadeOut(400, function() {
                    $(this).remove();
                });
            }, 5000);
            
            // Анимация прогресс-бара
            alert.find('.alert-progress').animate({width: '100%'}, 5000);
        }
    });
    
    // Закрытие сообщений по клику
    $('.alert .close').click(function() {
        $(this).closest('.alert').fadeOut(300, function() {
            $(this).remove();
        });
    });
    
    // ===========================================
    // ОБРАБОТКА ФОРМ
    // ===========================================
    
    // Улучшенная обработка отправки форм
    $('form').on('submit', function(e) {
        const form = $(this);
        const submitBtn = form.find('button[type="submit"]');
        
        // Проверяем, не является ли это формой с файлами
        const hasFiles = form.find('input[type="file"]').length > 0;
        
        if (submitBtn.length && !submitBtn.hasClass('no-loading')) {
            const originalText = submitBtn.text();
            const loadingText = submitBtn.data('loading-text') || 'Отправка...';
            
            submitBtn.addClass('loading')
                     .prop('disabled', true)
                     .text(loadingText);
            
            // Восстанавливаем кнопку через время (больше для файлов)
            const timeout = hasFiles ? 30000 : 10000;
            setTimeout(function() {
                submitBtn.removeClass('loading')
                         .prop('disabled', false)
                         .text(originalText);
            }, timeout);
        }
        
        // Валидация формы перед отправкой
        if (!validateForm(form)) {
            e.preventDefault();
            if (submitBtn.length) {
                submitBtn.removeClass('loading').prop('disabled', false);
            }
            return false;
        }
    });
    
    // ===========================================
    // ВАЛИДАЦИЯ ПОЛЕЙ
    // ===========================================
    
    // Валидация в реальном времени
    $('.form-control').on('blur', function() {
        validateField($(this));
    });
    
    $('.form-control').on('input', function() {
        const field = $(this);
        // Убираем ошибки при вводе
        if (field.hasClass('is-invalid')) {
            setTimeout(() => validateField(field), 500);
        }
    });
    
    // ===========================================
    // ЗАГРУЗКА ФАЙЛОВ
    // ===========================================
    
    // Обработка загрузки файлов
    $('input[type="file"]').on('change', function() {
        const input = $(this);
        const file = this.files[0];
        
        if (file) {
            const maxSize = parseInt(input.data('max-size')) || 5242880; // 5MB по умолчанию
            const allowedTypes = input.data('allowed-types');
            
            // Проверка размера файла
            if (file.size > maxSize) {
                showToast('Файл слишком большой. Максимальный размер: ' + formatFileSize(maxSize), 'error');
                input.val('');
                return;
            }
            
            // Проверка типа файла
            if (allowedTypes) {
                const types = allowedTypes.split(',').map(t => t.trim());
                if (!types.includes(file.type)) {
                    showToast('Недопустимый тип файла', 'error');
                    input.val('');
                    return;
                }
            }
            
            // Предварительный просмотр изображений
            if (file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    let preview = input.siblings('.file-preview');
                    if (!preview.length) {
                        preview = $('<div class="file-preview mt-2"></div>');
                        input.after(preview);
                    }
                    
                    preview.html(`
                        <div class="preview-container">
                            <img src="${e.target.result}" alt="Preview" class="preview-image">
                            <button type="button" class="btn-remove-preview" onclick="removePreview(this)">
                                <i class="fas fa-times"></i>
                            </button>
                        </div>
                    `);
                };
                reader.readAsDataURL(file);
            } else {
                // Показываем информацию о файле
                let preview = input.siblings('.file-preview');
                if (!preview.length) {
                    preview = $('<div class="file-preview mt-2"></div>');
                    input.after(preview);
                }
                
                preview.html(`
                    <div class="file-info">
                        <i class="fas fa-file"></i>
                        <span>${file.name}</span>
                        <small>(${formatFileSize(file.size)})</small>
                    </div>
                `);
            }
        }
    });
    
    // ===========================================
    // ПЛАВНАЯ ПРОКРУТКА
    // ===========================================
    
    // Плавная прокрутка для якорных ссылок
    $('a[href^="#"]').on('click', function(e) {
        const href = this.getAttribute('href');
        if (href === '#') return;
        
        const target = $(href);
        if (target.length) {
            e.preventDefault();
            const offsetTop = target.offset().top - 80; // Учитываем высоту навбара
            
            $('html, body').animate({
                scrollTop: offsetTop
            }, 800, 'easeInOutQuart');
        }
    });
    
    // ===========================================
    // ЛЕНИВАЯ ЗАГРУЗКА ИЗОБРАЖЕНИЙ
    // ===========================================
    
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    img.classList.add('loaded');
                    imageObserver.unobserve(img);
                }
            });
        }, {
            rootMargin: '50px 0px'
        });
        
        document.querySelectorAll('img[data-src]').forEach(img => {
            img.classList.add('lazy');
            imageObserver.observe(img);
        });
    }
    
    // ===========================================
    // ОБРАБОТКА ОШИБОК AJAX
    // ===========================================
    
    $(document).ajaxError(function(event, jqXHR, ajaxSettings, thrownError) {
        console.error('AJAX Error:', {
            status: jqXHR.status,
            url: ajaxSettings.url,
            error: thrownError
        });
        
        let message = 'Произошла ошибка';
        
        switch (jqXHR.status) {
            case 403:
                message = 'Доступ запрещен';
                break;
            case 404:
                message = 'Ресурс не найден';
                break;
            case 422:
                message = 'Ошибка валидации данных';
                break;
            case 500:
                message = 'Ошибка сервера. Попробуйте позже';
                break;
            case 0:
                message = 'Проблемы с соединением';
                break;
        }
        
        showToast(message, 'error');
    });
    
    // CSRF токен для AJAX запросов
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", $('[name=csrfmiddlewaretoken]').val());
            }
        }
    });
    
    // ===========================================
    // ПОДТВЕРЖДЕНИЕ ДЕЙСТВИЙ
    // ===========================================
    
    $('[data-confirm]').on('click', function(e) {
        const message = $(this).data('confirm') || 'Вы уверены?';
        if (!confirm(message)) {
            e.preventDefault();
            return false;
        }
    });
    
    // ===========================================
    // КОПИРОВАНИЕ В БУФЕР ОБМЕНА
    // ===========================================
    
    $('[data-copy]').on('click', function() {
        const text = $(this).data('copy');
        if (navigator.clipboard) {
            navigator.clipboard.writeText(text).then(() => {
                showToast('Скопировано в буфер обмена', 'success');
            }).catch(() => {
                fallbackCopyToClipboard(text);
            });
        } else {
            fallbackCopyToClipboard(text);
        }
    });
    
    // ===========================================
    // ОБРАБОТКА СОСТОЯНИЙ ЗАГРУЗКИ
    // ===========================================
    
    $('a[data-loading]').on('click', function() {
        const link = $(this);
        const originalText = link.text();
        const loadingText = link.data('loading') || 'Загрузка...';
        
        link.addClass('loading').text(loadingText);
        
        // Восстанавливаем через 5 секунд
        setTimeout(() => {
            link.removeClass('loading').text(originalText);
        }, 5000);
    });
    
    // ===========================================
    // АНИМАЦИИ ПРИ ПОЯВЛЕНИИ ЭЛЕМЕНТОВ
    // ===========================================
    
    if ('IntersectionObserver' in window) {
        const animationObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                }
            });
        }, {
            threshold: 0.1
        });
        
        document.querySelectorAll('.animate-on-scroll').forEach(el => {
            animationObserver.observe(el);
        });
    }
    
    // ===========================================
    // КЛАВИАТУРНАЯ НАВИГАЦИЯ
    // ===========================================
    
    $(document).keydown(function(e) {
        // ESC - закрыть модальные окна, поиск и т.д.
        if (e.key === 'Escape') {
            $('.search-form').removeClass('active');
            $('.dropdown').removeClass('show');
            $('.modal').modal('hide');
        }
        
        // Ctrl/Cmd + K - открыть поиск
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            if (typeof toggleSearch === 'function') {
                toggleSearch();
            }
        }
    });
});

// ===========================================
// ГЛОБАЛЬНЫЕ ФУНКЦИИ
// ===========================================

// Функция показа уведомлений
function showToast(message, type = 'info', duration = 4000) {
    const toastId = 'toast-' + Date.now();
    const toastHtml = `
        <div id="${toastId}" class="toast toast-${type}" style="
            position: fixed; 
            top: 20px; 
            right: 20px; 
            z-index: 9999; 
            background: white; 
            border-radius: 8px; 
            box-shadow: 0 4px 20px rgba(0,0,0,0.15); 
            padding: 16px 20px; 
            max-width: 400px; 
            border-left: 4px solid ${getToastColor(type)};
            transform: translateX(100%);
            transition: transform 0.3s ease;
        ">
            <div style="display: flex; align-items: center; gap: 12px;">
                <i class="fas ${getToastIcon(type)}" style="color: ${getToastColor(type)}; font-size: 16px;"></i>
                <span style="flex: 1; color: #212121; font-size: 14px; line-height: 1.4;">${message}</span>
                <button onclick="closeToast('${toastId}')" style="
                    background: none; 
                    border: none; 
                    color: #757575; 
                    cursor: pointer; 
                    padding: 4px; 
                    margin: -4px -4px -4px 8px;
                    border-radius: 4px;
                    transition: background-color 0.2s ease;
                " onmouseover="this.style.backgroundColor='#f5f5f5'" onmouseout="this.style.backgroundColor='transparent'">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        </div>
    `;
    
    $('body').append(toastHtml);
    
    // Анимация появления
    setTimeout(() => {
        $(`#${toastId}`).css('transform', 'translateX(0)');
    }, 10);
    
    // Автоматическое скрытие
    setTimeout(() => {
        closeToast(toastId);
    }, duration);
}

function closeToast(toastId) {
    const toast = $(`#${toastId}`);
    toast.css('transform', 'translateX(100%)');
    setTimeout(() => {
        toast.remove();
    }, 300);
}

function getToastColor(type) {
    const colors = {
        'success': '#4caf50',
        'error': '#f44336',
        'warning': '#ff9800',
        'info': '#2196f3'
    };
    return colors[type] || colors.info;
}

function getToastIcon(type) {
    const icons = {
        'success': 'fa-check-circle',
        'error': 'fa-exclamation-circle',
        'warning': 'fa-exclamation-triangle',
        'info': 'fa-info-circle'
    };
    return icons[type] || icons.info;
}

// Валидация полей
function validateField(field) {
    const value = field.val().trim();
    const type = field.attr('type');
    const required = field.prop('required');
    
    // Удаляем предыдущие ошибки
    field.removeClass('is-invalid is-valid');
    field.siblings('.invalid-feedback, .valid-feedback').remove();
    
    if (required && !value) {
        showFieldError(field, 'Это поле обязательно для заполнения');
        return false;
    }
    
    if (value) {
        if (type === 'email') {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(value)) {
                showFieldError(field, 'Введите корректный email адрес');
                return false;
            }
        }
        
        if (type === 'tel') {
            const phoneRegex = /^[\+]?[0-9\s\-\(\)]+$/;
            if (!phoneRegex.test(value) || value.replace(/\D/g, '').length < 10) {
                showFieldError(field, 'Введите корректный номер телефона');
                return false;
            }
        }
        
        if (type === 'url') {
            try {
                new URL(value);
            } catch {
                showFieldError(field, 'Введите корректный URL');
                return false;
            }
        }
        
        const minLength = parseInt(field.attr('minlength'));
        if (minLength && value.length < minLength) {
            showFieldError(field, `Минимальная длина: ${minLength} символов`);
            return false;
        }
        
        const maxLength = parseInt(field.attr('maxlength'));
        if (maxLength && value.length > maxLength) {
            showFieldError(field, `Максимальная длина: ${maxLength} символов`);
            return false;
        }
    }
    
    // Поле валидно
    field.addClass('is-valid');
    return true;
}

function showFieldError(field, message) {
    field.addClass('is-invalid');
    field.after(`<div class="invalid-feedback" style="display: block;">${message}</div>`);
}

// Валидация всей формы
function validateForm(form) {
    let isValid = true;
    
    form.find('.form-control[required], .form-control[type="email"], .form-control[minlength]').each(function() {
        if (!validateField($(this))) {
            isValid = false;
        }
    });
    
    // Проверяем пароли
    const password1 = form.find('input[name$="password1"]');
    const password2 = form.find('input[name$="password2"]');
    
    if (password1.length && password2.length) {
        if (password1.val() !== password2.val()) {
            showFieldError(password2, 'Пароли не совпадают');
            isValid = false;
        }
    }
    
    // Проверяем чекбоксы обязательных соглашений
    form.find('input[type="checkbox"][required]').each(function() {
        const checkbox = $(this);
        if (!checkbox.is(':checked')) {
            showFieldError(checkbox, 'Необходимо согласие');
            isValid = false;
        }
    });
    
    return isValid;
}

// Форматирование размера файла
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Функция для повторной отправки письма с подтверждением
window.resendVerification = function() {
    const button = $('[onclick="resendVerification()"]');
    const originalText = button.text();
    
    button.addClass('loading').prop('disabled', true).text('Отправка...');
    
    fetch('/users/resend-verification/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val(),
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Письмо с подтверждением отправлено на ваш email', 'success');
        } else {
            showToast('Произошла ошибка: ' + (data.error || 'Неизвестная ошибка'), 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Произошла ошибка при отправке письма', 'error');
    })
    .finally(() => {
        button.removeClass('loading').prop('disabled', false).text(originalText);
    });
};

// Переключение видимости пароля
window.togglePassword = function(fieldId, eyeId) {
    const field = document.getElementById(fieldId);
    const eye = document.getElementById(eyeId || 'password-eye');
    
    if (field.type === 'password') {
        field.type = 'text';
        eye.className = 'fas fa-eye-slash';
    } else {
        field.type = 'password';
        eye.className = 'fas fa-eye';
    }
};

// Удаление превью файла
window.removePreview = function(button) {
    const preview = $(button).closest('.file-preview');
    const input = preview.siblings('input[type="file"]');
    
    preview.remove();
    input.val('');
};

// Fallback для копирования в буфер обмена
function fallbackCopyToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.top = '0';
    textArea.style.left = '0';
    textArea.style.width = '2em';
    textArea.style.height = '2em';
    textArea.style.padding = '0';
    textArea.style.border = 'none';
    textArea.style.outline = 'none';
    textArea.style.boxShadow = 'none';
    textArea.style.background = 'transparent';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        document.execCommand('copy');
        showToast('Скопировано в буфер обмена', 'success');
    } catch (err) {
        showToast('Не удалось скопировать', 'error');
    }
    
    document.body.removeChild(textArea);
}

// Поиск (можно заменить на реальный API)
function performSearch(query, resultsContainer) {
    // Симуляция поиска - замените на реальный API
    const mockResults = [
        { id: 1, title: 'Металлообработка-2025', type: 'exhibition', url: '/exhibitions/1/' },
        { id: 2, title: 'IT конференция "Будущее технологий"', type: 'conference', url: '/conferences/1/' },
        { id: 3, title: 'Парксизан - выставка парков', type: 'exhibition', url: '/exhibitions/2/' },
        { id: 4, title: 'Wasma - водные технологии', type: 'exhibition', url: '/exhibitions/3/' },
        { id: 5, title: 'Строительные технологии 2025', type: 'exhibition', url: '/exhibitions/4/' }
    ].filter(item => item.title.toLowerCase().includes(query.toLowerCase()));
    
    resultsContainer.innerHTML = '';
    
    if (mockResults.length > 0) {
        mockResults.slice(0, 5).forEach(result => {
            const item = document.createElement('div');
            item.className = 'autocomplete-item';
            item.innerHTML = `
                <div style="display: flex; align-items: center; gap: 8px;">
                    <i class="fas ${result.type === 'exhibition' ? 'fa-calendar' : 'fa-microphone'}" style="color: #757575; width: 16px;"></i>
                    <span style="flex: 1;">${result.title}</span>
                    <small style="color: #9e9e9e;">${result.type === 'exhibition' ? 'Выставка' : 'Конференция'}</small>
                </div>
            `;
            
            item.addEventListener('click', function() {
                window.location.href = result.url;
            });
            
            item.addEventListener('mouseenter', function() {
                // Убираем активный класс с других элементов
                resultsContainer.querySelectorAll('.autocomplete-item').forEach(el => {
                    el.classList.remove('active');
                });
                // Добавляем активный класс текущему элементу
                this.classList.add('active');
            });
            
            resultsContainer.appendChild(item);
        });
        
        // Добавляем ссылку "Показать все результаты"
        if (mockResults.length > 5) {
            const showAllItem = document.createElement('div');
            showAllItem.className = 'autocomplete-item show-all';
            showAllItem.innerHTML = `
                <div style="text-align: center; color: #2196f3; font-weight: 500;">
                    <i class="fas fa-search mr-2"></i>
                    Показать все результаты (${mockResults.length})
                </div>
            `;
            showAllItem.addEventListener('click', function() {
                // Выполняем полный поиск
                document.querySelector('input[type="search"]').closest('form').submit();
            });
            resultsContainer.appendChild(showAllItem);
        }
        
        resultsContainer.style.display = 'block';
    } else {
        const noResults = document.createElement('div');
        noResults.className = 'autocomplete-item no-results';
        noResults.innerHTML = `
            <div style="text-align: center; color: #9e9e9e; font-style: italic;">
                <i class="fas fa-search mr-2"></i>
                Ничего не найдено
            </div>
        `;
        resultsContainer.appendChild(noResults);
        resultsContainer.style.display = 'block';
    }
}

// Создание конфетти для праздничных моментов
function createConfetti() {
    const colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#f9ca24', '#f0932b', '#6c5ce7', '#fd79a8'];
    const confettiCount = 50;
    
    for (let i = 0; i < confettiCount; i++) {
        setTimeout(() => {
            const confetti = $('<div>').css({
                position: 'fixed',
                top: '-10px',
                left: Math.random() * window.innerWidth + 'px',
                width: Math.random() * 8 + 6 + 'px',
                height: Math.random() * 8 + 6 + 'px',
                backgroundColor: colors[Math.floor(Math.random() * colors.length)],
                zIndex: 9999,
                borderRadius: Math.random() > 0.5 ? '50%' : '0',
                pointerEvents: 'none',
                transform: `rotate(${Math.random() * 360}deg)`
            });
            
            $('body').append(confetti);
            
            confetti.animate({
                top: window.innerHeight + 'px',
                left: '+=' + (Math.random() * 200 - 100) + 'px',
                opacity: 0,
                transform: `rotate(${Math.random() * 720}deg)`
            }, Math.random() * 2000 + 3000, function() {
                $(this).remove();
            });
        }, i * 100);
    }
}

// Функция для плавного обновления счетчиков
function animateCounter(element, target, duration = 2000) {
    const start = parseInt(element.textContent) || 0;
    const increment = (target - start) / (duration / 16);
    let current = start;
    
    const timer = setInterval(() => {
        current += increment;
        if ((increment > 0 && current >= target) || (increment < 0 && current <= target)) {
            current = target;
            clearInterval(timer);
        }
        element.textContent = Math.floor(current);
    }, 16);
}

// Функция для проверки видимости элемента
function isElementInViewport(el) {
    const rect = el.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}

// Функция для debounce (ограничение частоты вызовов)
function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction() {
        const context = this;
        const args = arguments;
        const later = function() {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func.apply(context, args);
    };
}

// Функция для throttle (ограничение частоты выполнения)
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Функция для получения cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Функция для установки cookie
function setCookie(name, value, days = 30) {
    const expires = new Date();
    expires.setTime(expires.getTime() + (days * 24 * 60 * 60 * 1000));
    document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/`;
}

// Проверка поддержки браузером различных возможностей
const browserSupport = {
    localStorage: (() => {
        try {
            return 'localStorage' in window && window['localStorage'] !== null;
        } catch (e) {
            return false;
        }
    })(),
    
    sessionStorage: (() => {
        try {
            return 'sessionStorage' in window && window['sessionStorage'] !== null;
        } catch (e) {
            return false;
        }
    })(),
    
    webp: (() => {
        const canvas = document.createElement('canvas');
        return canvas.toDataURL('image/webp').indexOf('image/webp') === 5;
    })(),
    
    touchDevice: 'ontouchstart' in window || navigator.maxTouchPoints > 0,
    
    reducedMotion: window.matchMedia('(prefers-reduced-motion: reduce)').matches
};

// Применяем классы к body в зависимости от поддержки браузера
$(document).ready(function() {
    const body = $('body');
    
    if (browserSupport.touchDevice) body.addClass('touch-device');
    if (browserSupport.webp) body.addClass('webp-support');
    if (browserSupport.reducedMotion) body.addClass('reduced-motion');
    if (!browserSupport.localStorage) body.addClass('no-local-storage');
});

// Обработка изменения размера окна
$(window).on('resize', debounce(function() {
    // Обновляем высоту элементов, которые зависят от размера окна
    const windowHeight = $(window).height();
    const windowWidth = $(window).width();
    
    // Закрываем мобильное меню при увеличении экрана
    if (windowWidth >= 992 && $('#navbarNav').hasClass('show')) {
        $('#navbarNav').removeClass('show');
        $('body').removeClass('menu-open');
        $('.navbar-toggler').removeClass('active');
    }
    
    // Обновляем позиционирование элементов
    $('.search-form.active').css('width', Math.min(320, windowWidth - 40));
}, 250));

// Обработка онлайн/офлайн статуса
window.addEventListener('online', function() {
    showToast('Соединение восстановлено', 'success', 2000);
});

window.addEventListener('offline', function() {
    showToast('Нет соединения с интернетом', 'warning', 5000);
});

// Предварительная загрузка важных страниц при наведении
$(document).on('mouseenter', 'a[href^="/"]', debounce(function() {
    const href = this.getAttribute('href');
    if (href && !href.includes('#') && !this.hasAttribute('data-no-prefetch')) {
        // Создаем невидимый link элемент для предварительной загрузки
        const link = document.createElement('link');
        link.rel = 'prefetch';
        link.href = href;
        document.head.appendChild(link);
        
        // Удаляем через некоторое время, чтобы не засорять head
        setTimeout(() => {
            if (link.parentNode) {
                link.parentNode.removeChild(link);
            }
        }, 5000);
    }
}, 1000));

// Обработка фокуса для улучшения доступности
$(document).on('keydown', function(e) {
    if (e.key === 'Tab') {
        $('body').addClass('using-keyboard');
    }
});

$(document).on('mousedown', function() {
    $('body').removeClass('using-keyboard');
});

// Защита от спама при отправке форм
const formSubmissionTracker = new Map();

$(document).on('submit', 'form', function(e) {
    const form = this;
    const formId = form.id || form.action || 'anonymous';
    const now = Date.now();
    const lastSubmission = formSubmissionTracker.get(formId);
    
    // Предотвращаем повторную отправку в течение 2 секунд
    if (lastSubmission && (now - lastSubmission) < 2000) {
        e.preventDefault();
        showToast('Подождите перед повторной отправкой', 'warning');
        return false;
    }
    
    formSubmissionTracker.set(formId, now);
});

// Очистка старых записей из трекера каждые 5 минут
setInterval(() => {
    const now = Date.now();
    formSubmissionTracker.forEach((timestamp, formId) => {
        if (now - timestamp > 300000) { // 5 минут
            formSubmissionTracker.delete(formId);
        }
    });
}, 300000);

// Инициализация всех компонентов после загрузки DOM
$(document).ready(function() {
    // Инициализируем tooltips если есть Bootstrap
    if (typeof $.fn.tooltip !== 'undefined') {
        $('[data-toggle="tooltip"]').tooltip();
    }
    
    // Инициализируем popovers если есть Bootstrap
    if (typeof $.fn.popover !== 'undefined') {
        $('[data-toggle="popover"]').popover();
    }
    
    // Добавляем smooth scroll behavior для браузеров, которые не поддерживают CSS scroll-behavior
    if (!CSS.supports('scroll-behavior', 'smooth')) {
        $('html').css('scroll-behavior', 'auto');
    }
    
    // Обновляем прогресс загрузки страницы
    $(window).on('load', function() {
        $('body').addClass('page-loaded');
        
        // Запускаем анимации счетчиков если они есть
        $('.counter').each(function() {
            const target = parseInt($(this).data('target'));
            if (target) {
                animateCounter(this, target);
            }
        });
    });
    
    console.log('ПП Expo - JavaScript инициализирован');
});