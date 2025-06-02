from django.shortcuts import render

def index(request):
    """Главная страница"""
    context = {
        'page_title': 'Главная страница',
    }
    return render(request, 'core/index.html', context)

