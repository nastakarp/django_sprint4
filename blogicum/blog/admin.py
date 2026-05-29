from django.contrib import admin
from .models import Post, Category, Location, Comment

# Регистрируем модели в админке
admin.site.register(Category)
admin.site.register(Location)
admin.site.register(Comment)

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'pub_date', 'is_published')
    list_editable = ('is_published',)
    search_fields = ('title',)
