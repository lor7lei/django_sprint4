from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import Http404

from .models import Post, Category, Comment
from .forms import PostForm, CommentForm

User = get_user_model()


def index(request):
    """Главная страница."""
    posts = Post.objects.filter(
        is_published=True,
        category__is_published=True,
        pub_date__lte=timezone.now()
    ).order_by('-pub_date')[:10]
    
    return render(request, 'blog/index.html', {'post_list': posts})


def post_detail(request, id):
    """Страница поста."""
    post = get_object_or_404(
        Post.objects.filter(
            is_published=True,
            category__is_published=True,
            pub_date__lte=timezone.now()
        ),
        pk=id
    )
    return render(request, 'blog/detail.html', {'post': post})


def category_posts(request, category_slug):
    """Посты категории."""
    category = get_object_or_404(
        Category.objects.filter(is_published=True),
        slug=category_slug
    )
    posts = Post.objects.filter(
        category=category,
        is_published=True,
        pub_date__lte=timezone.now()
    )
    return render(request, 'blog/category.html', {'category': category, 'post_list': posts})


def profile(request, username):
    """Профиль пользователя."""
    profile_user = get_object_or_404(User, username=username)
    return render(request, 'blog/profile.html', {'profile': profile_user})


@login_required
def edit_profile(request, username):
    """Редактирование профиля."""
    user = get_object_or_404(User, username=username)
    if request.user != user:
        return redirect('blog:profile', username=username)
    
    
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.save()
        return redirect('blog:profile', username=username)
 

    form_data = {
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
    }
    
    return render(request, 'blog/user.html', {'form': form_data, 'profile': user})


@login_required
def create_post(request):
    """Создание поста."""
    form = PostForm()
    return render(request, 'blog/create.html', {'form': form})


@login_required
def edit_post(request, id):
    """Редактирование поста."""
    post = get_object_or_404(Post, pk=id)
    if request.user != post.author:
        return redirect('blog:post_detail', id=id)
    
    form = PostForm(instance=post)
    return render(request, 'blog/create.html', {'form': form})


@login_required
def delete_post(request, id):
    """Удаление поста."""
    post = get_object_or_404(Post, pk=id)
    if request.user != post.author:
        return redirect('blog:post_detail', id=id)
    return render(request, 'blog/delete.html', {'post': post})


@login_required
def add_comment(request, id):
    """Добавление комментария."""
    post = get_object_or_404(Post, pk=id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
    return redirect('blog:post_detail', id=id)


@login_required
def edit_comment(request, id, comment_id):
    """Редактирование комментария."""
    comment = get_object_or_404(Comment, pk=comment_id, post_id=id)
    if request.user != comment.author:
        return redirect('blog:post_detail', id=id)
    
    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', id=id)
    
    form = CommentForm(instance=comment)
    return render(request, 'blog/comment.html', {'form': form, 'comment': comment})


@login_required
def delete_comment(request, id, comment_id):
    """Удаление комментария."""
    comment = get_object_or_404(Comment, pk=comment_id, post_id=id)
    if request.user != comment.author:
        return redirect('blog:post_detail', id=id)
    
    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', id=id)
    
    return render(request, 'blog/comment.html', {'comment': comment})