from multiprocessing import context
from django.shortcuts import render
from django.http import HttpResponse

def index(request):
    template = 'posts/index.html'
    title = "Это главная страница проекта Yatube"
    text = "Последние обновления на сайте"
    context = {
        'title':title,
        'text':text,
    }
    return render(request, template, context) 

def group_posts(request, slug):
    template = 'posts/group_list.html'
    title = "Здесь будет информация о группах проекта Yatube"
    context = {
        'title':title,
        'slug':slug,
    }
    return render(request, template, context) 

def group_list(request):
    template = 'posts/group_list.html'
    return render(request, template) 