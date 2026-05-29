from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils import timezone
from django.db.models import Count
from django.contrib.auth import get_user_model
from django.conf import settings
from django.http import Http404

from .models import Post, Category, Comment
from .forms import PostForm, CommentForm, UserForm

User = get_user_model()


# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ И МИКСИНЫ ---

def get_base_queryset():
    """Базовый запрос: посты с комментариями, отсортированные по дате."""
    return Post.objects.select_related(
        'category', 'location', 'author'
    ).annotate(comment_count=Count('comments')).order_by('-pub_date')


def get_public_queryset():
    """Только опубликованные посты с датой публикации <= сейчас."""
    return get_base_queryset().filter(
        is_published=True,
        category__is_published=True,
        pub_date__lte=timezone.now()
    )


class AuthorRequiredMixin(UserPassesTestMixin):
    """Миксин: разрешает доступ только автору объекта."""

    def test_func(self):
        obj = self.get_object()
        return obj.author == self.request.user


# --- ПРЕДСТАВЛЕНИЯ ДЛЯ ПОСТОВ (ГЛАВНАЯ И КАТЕГОРИИ) ---

class IndexListView(ListView):
    """Главная страница."""
    model = Post
    template_name = 'blog/index.html'
    paginate_by = settings.PAGINATE_BY

    def get_queryset(self):
        return get_public_queryset()


class CategoryPostsView(ListView):
    """Страница категории."""
    model = Post
    template_name = 'blog/category.html'
    paginate_by = settings.PAGINATE_BY

    def get_queryset(self):
        self.category = get_object_or_404(
            Category, slug=self.kwargs['category_slug'], is_published=True
        )
        return get_public_queryset().filter(category=self.category)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context


# --- ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ ---

class ProfileView(ListView):
    """Профиль пользователя."""
    model = Post
    template_name = 'blog/profile.html'
    paginate_by = settings.PAGINATE_BY

    def get_queryset(self):
        self.profile_user = get_object_or_404(User, username=self.kwargs['username'])
        # Если пользователь смотрит свой профиль — показываем все его посты
        if self.request.user == self.profile_user:
            return get_base_queryset().filter(author=self.profile_user)
        # Если чужой — только опубликованные
        return get_public_queryset().filter(author=self.profile_user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.profile_user
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование профиля."""
    model = User
    form_class = UserForm
    template_name = 'blog/user.html'

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        return reverse('blog:profile', kwargs={'username': self.request.user.username})


class PostDetailView(DetailView):
    """Просмотр поста и комментариев."""
    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def get_queryset(self):
        return get_base_queryset()

    def get_object(self, queryset=None):
        # Получаем пост по ID
        obj = super().get_object(queryset)
        # Если пост не опубликован, либо категория скрыта, либо время публикации еще не пришло:
        if not obj.is_published or not obj.category.is_published or obj.pub_date > timezone.now():
            # Доступ к такому посту имеет ТОЛЬКО его автор
            if obj.author != self.request.user:
                raise Http404("Пост не найден")
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.object.comments.select_related('author')
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    """Создание поста."""
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:profile', kwargs={'username': self.request.user.username})


class PostUpdateView(LoginRequiredMixin, AuthorRequiredMixin, UpdateView):
    """Редактирование поста."""
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def handle_no_permission(self):
        # Перенаправляем не-автора на страницу поста
        return redirect('blog:post_detail', post_id=self.kwargs['post_id'])

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'post_id': self.object.id})


class PostDeleteView(LoginRequiredMixin, AuthorRequiredMixin, DeleteView):
    """Удаление поста."""
    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Отправляем форму в контекст, чтобы шаблон мог ее отрисовать для подтверждения
        context['form'] = PostForm(instance=self.object)
        return context

    def get_success_url(self):
        return reverse('blog:profile', kwargs={'username': self.request.user.username})


# --- CRUD ДЛЯ КОММЕНТАРИЕВ ---

class CommentCreateView(LoginRequiredMixin, CreateView):
    """Добавление комментария."""
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(Post, pk=self.kwargs['post_id'])
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'post_id': self.kwargs['post_id']})


class CommentUpdateView(LoginRequiredMixin, AuthorRequiredMixin, UpdateView):
    """Редактирование комментария."""
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'post_id': self.object.post.id})


class CommentDeleteView(LoginRequiredMixin, AuthorRequiredMixin, DeleteView):
    """Удаление комментария."""
    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'post_id': self.object.post.id})
