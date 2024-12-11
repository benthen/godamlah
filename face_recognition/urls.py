from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = "face_recognition"

urlpatterns = [
    path('', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('verify/<int:user_id>/', views.verify, name='verify'),
    path('capture_voice/', views.capture_voice_view, name='capture_voice'),
    path('video_feed/', views.video_feed, name='video_feed'),
    path('home/', views.home_view, name='home'),
    # path('activate/<uidb64>/<token>', views.activate, name='activate'),
    # path('profile/<str:username>', views.set_password, name='password'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
