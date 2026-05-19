from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from road_api.views import get_roads_json
from road_api.views import (
    RoadViewSet, RouteViewSet, WeatherViewSet, EmergencyWarningViewSet,
    DangerousAreaViewSet, NotificationViewSet, UserRegistrationViewSet,
    UserMessageViewSet, UserMessageReactionViewSet, UserMessageCommentViewSet,
    index, road_status_view, register_view, profile_view, current_user_view,
    logout_view
)

router = DefaultRouter()
router.register(r'roads', RoadViewSet)
router.register(r'routes', RouteViewSet)
router.register(r'weather', WeatherViewSet)
router.register(r'warnings', EmergencyWarningViewSet)
router.register(r'dangerous-areas', DangerousAreaViewSet)
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'users', UserRegistrationViewSet)
router.register(r'user-messages', UserMessageViewSet)
router.register(r'user-message-reactions', UserMessageReactionViewSet, basename='user-message-reaction')
router.register(r'user-message-comments', UserMessageCommentViewSet, basename='user-message-comment')

urlpatterns = [
    path('', index), # Главная страница
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
    path('api-token-auth/', obtain_auth_token),  # Получение токена
    path('api/auth/user/', current_user_view),
    path('accounts/register/', register_view, name='register'),
    path('accounts/profile/', profile_view, name='profile'),
    path('road-status/', road_status_view, name='road_status'),
    path('accounts/logout/', logout_view, name='logout'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('api/roads_config/', get_roads_json, name='roads_json'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
