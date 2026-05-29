from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import Post, Comment, User

User = get_user_model()

class PostForm(forms.ModelForm):
    """Форма для создания и редактирования публикации."""
    class Meta:
        model = Post
        exclude = ('author',)
        widgets = {
            'pub_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class CommentForm(forms.ModelForm):
    """Форма для добавления комментария."""
    class Meta:
        model = Comment
        fields = ('text',)

class ProfileForm(forms.ModelForm):
    """Форма для редактирования профиля пользователя."""
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')

class CustomUserCreationForm(UserCreationForm):
    """Форма для регистрации пользователя."""
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')
