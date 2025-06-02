    // Активация карусели
    $(document).ready(function() {
        $('#exhibitionCarousel').carousel({
            interval: 5000
        });
        
        // Анимация появления карточек при скролле
        $(window).scroll(function() {
            $('.exhibition-card-wrapper').each(function() {
                var position = $(this).offset().top;
                var scrollPosition = $(window).scrollTop() + $(window).height();
                
                if (position < scrollPosition) {
                    $(this).addClass('visible');
                }
            });
        });
        
        // Запуск проверки видимости элементов при загрузке страницы
        $(window).scroll();
    });

    // Плавная прокрутка для якорных ссылок
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener("click", function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute("href"));
            if (target) {
                window.scrollTo({
                    top: target.offsetTop - 80, // 80px отступ (можно изменить)
                    behavior: "smooth"
                });
            }
        });
    });

    $(document).ready(function() {
        $('#exhibitionCarousel').carousel({
            interval: 5000
        });
        
        // Анимация появления карточек при скролле
        $(window).scroll(function() {
            $('.exhibition-card-wrapper, .timeline-item, .testimonial-card').each(function() {
                var position = $(this).offset().top;
                var scrollPosition = $(window).scrollTop() + $(window).height() - 100;
                
                if (position < scrollPosition) {
                    $(this).addClass('visible');
                }
            });
        });
        
        // Запуск проверки видимости элементов при загрузке страницы
        $(window).scroll();
    });

    // Плавная прокрутка для якорных ссылок
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener("click", function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute("href"));
            if (target) {
                window.scrollTo({
                    top: target.offsetTop - 80,
                    behavior: "smooth"
                });
            }
        });
    });
    
    // Добавляем анимацию для фильтра категорий
    $('.filter-badge').on('click', function() {
        $('.filter-badge').removeClass('active');
        $(this).addClass('active');
    });
