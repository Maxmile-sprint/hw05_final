from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.cache import cache_page
from .forms import PostForm, CommentForm
from .models import Post, Group, Follow
from .utils import get_page_obj

User = get_user_model()


@cache_page(20)
def index(request):

    page_obj = get_page_obj(Post.objects.all(), request)

    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)

    page_obj = get_page_obj(group.posts_grp.all(), request)

    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)

    posts_count = author.posts_usr.all().count()

    page_obj = get_page_obj(author.posts_usr.all(), request)

    following = request.user.is_authenticated and Follow.objects.filter(
        user=request.user, author=author).exists()

    context = {
        'page_obj': page_obj,
        'posts_count': posts_count,
        'author': author,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post_obj = get_object_or_404(Post, pk=post_id)
    posts_count = Post.objects.filter(author_id=post_obj.author_id).count()
    form = CommentForm()
    comments = post_obj.comments.all()

    context = {
        'post_obj': post_obj,
        'posts_count': posts_count,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    group_option = Group.objects.all()
    user = get_object_or_404(User, username=request.user)

    form = PostForm(request.POST or None, files=request.FILES or None)

    title = 'Добавить запись'

    if request.method != 'POST':

        context = {
            'form': form,
            'title': title,
            'group_option': group_option
        }
        return render(request, 'posts/create_post.html', context)

    if form.is_valid():
        temp_form = form.save(commit=False)
        temp_form.author = user
        temp_form.save()

        return redirect('posts:profile', username=request.user)

    context = {
        'form': form,
        'title': title,
        'group_option': group_option
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)

    is_edit = True
    title = 'Редактировать запись'

    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )

    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)

    context = {
        'post_id': post_id,
        'form': form,
        'is_edit': is_edit,
        'title': title,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    current_user = request.user

    authors = list(current_user.follower.values_list('author', flat=True))

    page_obj = get_page_obj(
        Post.objects.filter(author_id__in=authors), request)

    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    if user != author:
        Follow.objects.get_or_create(user=user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    Follow.objects.get(user=user, author=author).delete()
    return redirect('posts:profile', username=username)
