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
from django.views.decorators.csrf import csrf_exempt  
User = get_user_model()


def index(request):
    """Главная страница."""
    print("=== INDEX VIEW CALLED ===")
    posts = Post.objects.filter(
        is_published=True,
        category__is_published=True,
        pub_date__lte=timezone.now()
    ).annotate(
        comment_count=Count('comments')
    ).order_by('-pub_date')
    
    print(f"Найдено постов: {posts.count()}")
    
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'blog/index.html', {'page_obj': page_obj})


def profile(request, username):
    profile_user = get_object_or_404(User, username=username)
    
    if request.user == profile_user:
        posts = Post.objects.filter(
            author=profile_user
        ).annotate(
            comment_count=Count('comments')
        ).order_by('-pub_date')
    else:
        posts = Post.objects.filter(
            author=profile_user,
            is_published=True,
            category__is_published=True,
            pub_date__lte=timezone.now()
        ).annotate(
            comment_count=Count('comments')
        ).order_by('-pub_date')
    
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'blog/profile.html', {
        'profile': profile_user,
        'page_obj': page_obj
    })


@login_required
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
    ).annotate(
        comment_count=Count('comments')
    ).order_by('-pub_date')
    
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'blog/category.html', {
        'category': category,
        'page_obj': page_obj
    })


@login_required
def post_detail(request, id):
    post = get_object_or_404(Post, pk=id)
    
    # Если пост не опубликован и пользователь не автор - 404
    if not post.is_published and request.user != post.author:
        raise Http404("Пост не найден")
    
    comments = post.comments.filter(is_published=True)
    form = CommentForm() if request.user.is_authenticated else None
    
    return render(request, 'blog/detail.html', {
        'post': post,
        'comments': comments,
        'form': form
    })



@login_required
def edit_profile(request, username):
    print(f"\n=== EDIT PROFILE ===")
    print(f"username: {username}")
    print(f"request.user: {request.user}")
    
    user = get_object_or_404(User, username=username)
    print(f"user found: {user}")
    
    if request.user != user:
        print(f"NOT OWNER - redirect to profile")
        return redirect('blog:profile', username=username)
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=user)
        print(f"POST data: {request.POST}")
        print(f"form is_valid: {form.is_valid()}")
        print(f"form errors: {form.errors}")
        if form.is_valid():
            form.save()
            print(f"PROFILE SAVED")
            return redirect('blog:profile', username=username)
    else:
        form = ProfileForm(instance=user)
        print(f"GET request - showing form")
    
    return render(request, 'blog/user.html', {'form': form, 'profile': user})


@login_required
def add_comment(request, id):
    print(f"\n=== ADD COMMENT ===")
    print(f"post_id: {id}")
    print(f"method: {request.method}")
    
    try:
        post = Post.objects.get(pk=id)
        print(f"post found: {post}")
    except Post.DoesNotExist:
        print(f"post NOT FOUND - raising 404")
        raise Http404("Пост не найден")
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        print(f"POST data: {request.POST}")
        print(f"form is_valid: {form.is_valid()}")
        print(f"form errors: {form.errors}")
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
            print(f"COMMENT SAVED with id: {comment.id}")
            return redirect('blog:post_detail', id=id)
        else:
            print(f"FORM INVALID - redirecting")
    else:
        print(f"GET request - redirecting")
    
    return redirect('blog:post_detail', id=id)


@login_required
def create_post(request):
    print(f"\n=== CREATE POST ===")
    print(f"method: {request.method}")
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        print(f"POST data: {request.POST}")
        print(f"FILES: {request.FILES}")
        print(f"form is_valid: {form.is_valid()}")
        print(f"form errors: {form.errors}")
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            print(f"POST SAVED with id: {post.id}")
            return redirect('blog:profile', username=request.user.username)
    else:
        form = PostForm()
        print(f"GET request - showing form")
    
    return render(request, 'blog/create.html', {'form': form})


@login_required
def edit_post(request, id):
    """Редактирование поста."""
    post = get_object_or_404(Post, pk=id)
    if request.user != post.author:
        return redirect('blog:post_detail', id=id)
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', id=id)
    else:
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
def edit_comment(request, id, comment_id):
    """Редактирование комментария."""
    comment = get_object_or_404(Comment, pk=comment_id, post_id=id)
    if request.user != comment.author:
        return redirect('blog:post_detail', id=id)
    
    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()  # updated_at обновится автоматически
            return redirect('blog:post_detail', id=id)
    else:
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