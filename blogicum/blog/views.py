from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.core.paginator import Paginator
from django.contrib import messages  
from .models import Post, Category, Comment
from django.db.models import Count
from .forms import PostForm, CommentForm, ProfileForm  

User = get_user_model()


++ # ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (Пункт 5) ==========
++ 
++ def get_published_posts():
++     """Возвращает QuerySet опубликованных постов."""
++     return Post.objects.filter(
++         is_published=True,
++         category__is_published=True,
++         pub_date__lte=timezone.now()
++     ).select_related('author', 'category').annotate(
++         comment_count=Count('comments')
++     ).order_by('-pub_date')
++ 
++ 
++ def get_user_posts(user, viewer=None):
++     """
++     Возвращает посты пользователя с учетом прав просматривающего.
++     viewer - кто смотрит (request.user)
++     """
++     if viewer == user:
++         # Автор видит все свои посты
++         return Post.objects.filter(
++             author=user
++         ).select_related('author', 'category').annotate(
++             comment_count=Count('comments')
++         ).order_by('-pub_date')
++     else:
++         # Остальные видят только опубликованные
++         return get_published_posts().filter(author=user)
++ 
++ 
++ def paginate_queryset(request, queryset, items_per_page=10):
++     """Пагинация queryset."""
++     paginator = Paginator(queryset, items_per_page)
++     page_number = request.GET.get('page')
++     page_obj = paginator.get_page(page_number)
++     return page_obj
++ 
++ 
++ # ========== ОСНОВНЫЕ ВЬЮХИ ==========


def index(request):
    """Главная страница."""
++  posts = get_published_posts()
++  page_obj = paginate_queryset(request, posts)
    return render(request, 'blog/index.html', {'page_obj': page_obj})


def profile(request, username):
    profile_user = get_object_or_404(User, username=username)
    
++  # Получаем посты пользователя с учетом прав
++  posts = get_user_posts(profile_user, viewer=request.user)
++  page_obj = paginate_queryset(request, posts)
    
    return render(request, 'blog/profile.html', {
        'profile': profile_user,
        'page_obj': page_obj
    })


def category_posts(request, category_slug):
    """Посты категории."""
    category = get_object_or_404(
++      Category,
        slug=category_slug,
++      is_published=True  # Проверяем сразу в get_object_or_404
    )
++  # Только опубликованные посты в опубликованной категории
++  posts = get_published_posts().filter(category=category)
++  page_obj = paginate_queryset(request, posts)
    
    return render(request, 'blog/category.html', {
        'category': category,
        'page_obj': page_obj
    })


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    
    # Если пользователь не автор - проверяем все условия публикации
    if request.user != post.author:
        # Проверяем: опубликован ли пост, опубликована ли категория, наступила ли дата
        if not (post.is_published and 
                post.category.is_published and 
                post.pub_date <= timezone.now()):
            raise Http404("Пост не найден или недоступен")
    
    comments = post.comments.filter(is_published=True)
    form = CommentForm() if request.user.is_authenticated else None
    
    return render(request, 'blog/detail.html', {
        'post': post,
        'comments': comments,
        'form': form
    })


@login_required
def edit_profile(request, username):
    user = get_object_or_404(User, username=username)
    
    if request.user != user:
        return redirect('blog:profile', username=username)
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('blog:profile', username=username)
    else:
        form = ProfileForm(instance=user)
    
    return render(request, 'blog/user.html', {'form': form, 'profile': user})


@login_required
def add_comment(request, post_id):
    try:
        post = Post.objects.get(pk=post_id)
    except Post.DoesNotExist:
        raise Http404("Пост не найден")
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
            return redirect('blog:post_detail', post_id=post_id)
        else:
            print(f"FORM INVALID - redirecting")
    else:
        print(f"GET request - redirecting")
    
    return redirect('blog:post_detail', post_id=post_id)


@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('blog:profile', username=request.user.username)
    else:
        form = PostForm()
    
    return render(request, 'blog/create.html', {'form': form})


@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('blog:post_detail', post_id=post_id)
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id=post_id)
    else:
        form = PostForm(instance=post)
    
    return render(request, 'blog/create.html', {'form': form})


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        messages.error(request, 'У вас нет прав для удаления этого поста')
        return redirect('blog:post_detail', post_id=post_id)
    
    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Пост успешно удален')
        return redirect('blog:profile', username=request.user.username)
    
    return render(request, 'blog/delete_confirm.html', {'post': post})


@login_required
def edit_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id, post_id=post_id)
    if request.user != comment.author:
        return redirect('blog:post_detail', post_id=post_id)
    
    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id=post_id)
    else:
        form = CommentForm(instance=comment)
    
    return render(request, 'blog/comment.html', {'form': form, 'comment': comment})


@login_required
def delete_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id, post_id=post_id)
    if request.user != comment.author:
        return redirect('blog:post_detail', post_id=post_id)
    
    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', post_id=post_id)
    
    return render(request, 'blog/comment.html', {'comment': comment})