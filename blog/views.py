from django.shortcuts import render, get_object_or_404
from .models import Post
from django.utils import timezone
from django.views.generic.base import TemplateView

# Create your views here.

class HomePage(TemplateView):
    template_name = 'blog/home.html'

def post_list(request):
    posts = Post.objects.all()
    return render(request, 'blog/post_list.html', {'posts': posts})

def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    return render(request, 'blog/post_detail.html', {'post': post})

def contact_us(request):
    return render(request, 'blog/contact_us.html', {})


'''

def post_category(request, category):
    posts = Post.objects.filter()
    return render(request, 'blog/category_list.html', {'category': category}) 

'''