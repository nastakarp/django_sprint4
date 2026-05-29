from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.utils import timezone
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from .models import Post, Category, Comment
from .forms import PostForm, CommentForm, ProfileForm, CustomUserCreationForm

User = get_user_model()

def get_posts_queryset():
    """Возвращает опубликованные посты с датой в прошлом."""
    return Post.objects.filter(
        is_published=True,
        pub_date__lte=timezone.now(),
        category__is_published=True
    ).select_related('category', 'location', 'author').annotate(comment_count=Count('comments'))

class AuthorRequiredMixin(UserPassesTestMixin):
    """Миксин для проверки, является ли пользователь автором объекта."""
    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

class IndexView(ListView):
    """Главная страница с публикациями."""
    model = Post
    template_name = 'blog/index.html'
    paginate_by = 10

    def get_queryset(self):
        return get_posts_queryset()

class PostDetailView(DetailView):
    """Страница отдельной публикации."""
    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.get_object()
        context['comments'] = post.comments.select_related('author').all()
        context['form'] = CommentForm()
        return context

class PostCreateView(LoginRequiredMixin, CreateView):
    """Страница создания публикации."""
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:profile', kwargs={'username': self.request.user.username})

class PostUpdateView(LoginRequiredMixin, AuthorRequiredMixin, UpdateView):
    """Страница редактирования публикации."""
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'post_id': self.object.pk})

class PostDeleteView(LoginRequiredMixin, AuthorRequiredMixin, DeleteView):
    """Страница удаления публикации."""
    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.object.comments.all()
        return context

    def get_success_url(self):
        return reverse('blog:index')

@login_required
def add_comment(request, post_id):
    """Добавление комментария к публикации."""
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('blog:post_detail', post_id=post_id)

class CommentUpdateView(LoginRequiredMixin, AuthorRequiredMixin, UpdateView):
    """Страница редактирования комментария."""
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'post_id': self.object.post.pk})

class CommentDeleteView(LoginRequiredMixin, AuthorRequiredMixin, DeleteView):
    """Страница удаления комментария."""
    model = Comment
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'comment_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['post'] = self.object.post
        context['comments'] = self.object.post.comments.all()
        context['form'] = CommentForm()
        return context

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'post_id': self.object.post.pk})

class ProfileView(ListView):
    """Страница профиля пользователя."""
    model = Post
    template_name = 'blog/profile.html'
    paginate_by = 10

    def get_queryset(self):
        self.profile_user = get_object_or_404(User, username=self.kwargs['username'])
        if self.request.user == self.profile_user:
            # Автор видит все свои посты, включая отложенные
            return Post.objects.filter(
                author=self.profile_user
            ).select_related('category', 'location').annotate(comment_count=Count('comments'))
        # Другие пользователи видят только опубликованные
        return get_posts_queryset().filter(author=self.profile_user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.profile_user
        return context

class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Страница редактирования профиля."""
    model = User
    form_class = ProfileForm
    template_name = 'blog/user.html'

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse('blog:profile', kwargs={'username': self.request.user.username})

class RegisterView(CreateView):
    """Страница регистрации пользователя."""
    template_name = 'registration/registration_form.html'
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('blog:login')

class CategoryPostsListView(ListView):
    """Страница публикаций категории."""
    model = Post
    template_name = 'blog/category.html'
    paginate_by = 10

    def get_queryset(self):
        self.category = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True
        )
        return get_posts_queryset().filter(category=self.category)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context

def page_not_found(request, exception):
    """Обработчик ошибки 404."""
    return render(request, 'pages/404.html', status=404)

def server_error(request):
    """Обработчик ошибки 500."""
    return render(request, 'pages/500.html', status=500)

def csrf_failure(request, reason=""):
    """Обработчик ошибки 403 CSRF."""
    return render(request, 'pages/403csrf.html', status=403)
