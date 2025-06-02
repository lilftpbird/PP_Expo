$(document).ready(function() {
    // Исправление для мобильного меню
    $('.navbar-toggler').click(function(e) {
        e.preventDefault();
        $('#navbarNav').toggleClass('show');
        $('body').toggleClass('menu-open');
    });
    
    // Закрытие меню при клике вне его
    $(document).on('click', function(e) {
        if (!$(e.target).closest('.navbar-collapse').length && 
            !$(e.target).closest('.navbar-toggler').length && 
            $('#navbarNav').hasClass('show')) {
            $('#navbarNav').removeClass('show');
            $('body').removeClass('menu-open');
        }
    });
    
    // Обработка выпадающих меню на мобильных устройствах
    $('.dropdown-toggle').click(function(e) {
        if (window.innerWidth < 992) {
            e.preventDefault();
            $(this).next('.dropdown-menu').toggleClass('show');
        }
    });
    
    // Функция для поиска
    window.toggleSearch = function() {
        $('.search-form').toggleClass('active');
        if ($('.search-form').hasClass('active')) {
            setTimeout(function() {
                $('.search-form input').focus();
            }, 300);
        }
    };
    
    // Изменение стиля навбара при прокрутке
    $(window).scroll(function() {
        if ($(window).scrollTop() > 50) {
            $('.navbar').css({
                'padding': '10px 0',
                'background-color': 'rgba(33, 33, 33, 0.95)'
            });
        } else {
            $('.navbar').css({
                'padding': '15px 0',
                'background-color': '#212121'
            });
        }
    });
    
    // Автозаполнение поиска
    const searchInput = document.querySelector('input[type="search"]');
    if (searchInput) {
        const autocompleteResults = document.createElement('div');
        autocompleteResults.className = 'autocomplete-results';
        searchInput.parentNode.appendChild(autocompleteResults);
        
        searchInput.addEventListener('input', function() {
            const query = this.value.trim();
            
            if (query.length < 2) {
                autocompleteResults.innerHTML = '';
                autocompleteResults.style.display = 'none';
                return;
            }
            
            // Симуляция результатов поиска
            const mockResults = [
                { id: 1, title: 'Металлообработка-2025' },
                { id: 2, title: 'Парксизан' },
                { id: 3, title: 'Wasma' }
            ].filter(item => item.title.toLowerCase().includes(query.toLowerCase()));
            
            autocompleteResults.innerHTML = '';
            
            if (mockResults.length > 0) {
                mockResults.forEach(result => {
                    const item = document.createElement('div');
                    item.className = 'autocomplete-item';
                    item.textContent = result.title;
                    item.addEventListener('click', function() {
                        searchInput.value = result.title;
                        autocompleteResults.style.display = 'none';
                    });
                    autocompleteResults.appendChild(item);
                });
                autocompleteResults.style.display = 'block';
            } else {
                autocompleteResults.style.display = 'none';
            }
        });
        
        // Скрываем автозаполнение при клике вне его
        document.addEventListener('click', function(e) {
            if (e.target !== searchInput) {
                autocompleteResults.style.display = 'none';
            }
        });
    }
});