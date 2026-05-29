from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Импортируем views из приложения blog
from blog import views

# Обработчики ошибок
handler404 = 'blog.views.page_not_found'
handler500 = 'blog.views.server_error'
handler403 = 'blog.views.csrf_failure'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('pages/', include('pages.urls', namespace='pages')),
    path('', include('blog.urls', namespace='blog')),
    path('auth/', include('django.contrib.auth.urls')),
    path('auth/registration/', views.RegisterView.as_view(), name='registration'),
]

# Раздача медиа-файлов только в режиме отладки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
