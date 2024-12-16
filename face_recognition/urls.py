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
    path('home/<int:user_id>/', views.home_view, name='home'),
    path('otp/<int:user_id>', views.otp_view, name='otp'),
    path("check-password-hygiene/", views.check_password_hygiene, name='check_password_hygiene'),
    path('question/<int:user_id>/<int:question_id>/', views.question_page, name='question_page'),
    path('submit-answers/', views.submit_answers, name='submit_answers'),
    # path('activate/<uidb64>/<token>', views.activate, name='activate'),
    # path('profile/<str:username>', views.set_password, name='password'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
