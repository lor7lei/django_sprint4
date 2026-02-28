from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import Http404
from .models import Post, Category, Comment
from .forms import PostForm, CommentForm, ProfileForm

User = get_user_model()


def index(request):
    """Главная страница."""
    print("=== INDEX VIEW CALLED ===")
    posts = Post.objects.filter(
        is_published=True,
        category__is_published=True,
        pub_date__lte=timezone.now()
    ).order_by('-pub_date')[:10]
    
    print(f"Найдено постов: {posts.count()}")
    for post in posts:
        print(f"Пост: {post.title}, дата: {post.pub_date}")
    
    return render(request, 'blog/index.html', {'page_obj': posts})


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
    
    # Получаем комментарии к посту
    comments = post.comments.filter(is_published=True)
    
    # Форма для комментария (если пользователь авторизован)
    form = None
    if request.user.is_authenticated:
        form = CommentForm()
    
    return render(request, 'blog/detail.html', {
        'post': post,
        'comments': comments,
        'form': form
    })


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
    ).order_by('-pub_date')
    
    return render(request, 'blog/category.html', {
        'category': category,
        'page_obj': posts  # ← ВАЖНО!
    })


def profile(request, username):
    """Профиль пользователя."""
    profile_user = get_object_or_404(User, username=username)
    
    # Получаем посты пользователя
    posts = Post.objects.filter(
        author=profile_user,
        is_published=True,
        category__is_published=True,
        pub_date__lte=timezone.now()
    ).order_by('-pub_date')
    
    return render(request, 'blog/profile.html', {
        'profile': profile_user,
        'page_obj': posts  # ← ВАЖНО!
    })


@login_required
def edit_profile(request, username):
    """Редактирование профиля."""
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