from django.contrib import admin

from .models import Location, Category, Post, Comment

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_published', 'pub_date')
    list_editable = ('is_published',)
    ordering = ('-pub_date',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'is_published', 'pub_date')
    list_editable = ('is_published',)
    ordering = ('-pub_date',)

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'is_published', 'pub_date')
    list_editable = ('is_published',)
    ordering = ('-pub_date',)
    list_filter = ('category', 'location', 'author')

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('text', 'author', 'post', 'created_at')
    list_filter = ('post', 'author', 'created_at')
    ordering = ('-created_at',)
