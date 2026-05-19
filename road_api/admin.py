from django.contrib import admin
from .models import (
    Road, Route, Weather, EmergencyWarning, 
    DangerousArea, Notification, UserProfile, UserMessage
)

# Route Admin
@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_lat', 'start_lng', 'end_lat', 'end_lng', 'created_at', 'user')
    search_fields = ('name',)
    list_filter = ('created_at',)


# Road Admin
@admin.register(Road)
class RoadAdmin(admin.ModelAdmin):
    # Какие колонки показывать в списке
    list_display = ('name', 'route', 'status', 'author', 'created_at')
    
    # По каким полям можно искать
    search_fields = ('name', 'route__name')
    
    # Фильтры справа
    list_filter = ('status', 'route', 'created_at')
    readonly_fields = ('created_at', 'updated_at')


# Weather Admin
@admin.register(Weather)
class WeatherAdmin(admin.ModelAdmin):
    list_display = ('road', 'temperature', 'precipitation', 'wind_speed', 'ice_probability', 'measured_at')
    search_fields = ('road__name',)
    list_filter = ('precipitation', 'measured_at')
    readonly_fields = ('measured_at', 'updated_at')


# Emergency Warning Admin
@admin.register(EmergencyWarning)
class EmergencyWarningAdmin(admin.ModelAdmin):
    list_display = ('title', 'road', 'warning_type', 'severity', 'author', 'created_at', 'resolved_at')
    search_fields = ('title', 'description', 'road__name')
    list_filter = ('warning_type', 'severity', 'created_at', 'resolved_at')
    readonly_fields = ('created_at',)


# Dangerous Area Admin
@admin.register(DangerousArea)
class DangerousAreaAdmin(admin.ModelAdmin):
    list_display = ('road', 'danger_type', 'location', 'author', 'created_at', 'resolved_at')
    search_fields = ('location', 'description', 'road__name')
    list_filter = ('danger_type', 'created_at', 'resolved_at')
    readonly_fields = ('created_at',)


# Notification Admin
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'notification_type', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'user__username')
    list_filter = ('notification_type', 'is_read', 'created_at')
    readonly_fields = ('created_at',)


# User Profile Admin
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'city', 'notification_enabled', 'created_at')
    search_fields = ('user__username', 'user__email', 'phone', 'city')
    list_filter = ('notification_enabled', 'created_at')
    readonly_fields = ('created_at',)


# UserMessage Admin
@admin.register(UserMessage)
class UserMessageAdmin(admin.ModelAdmin):
    list_display = ('title', 'message_type', 'user', 'latitude', 'longitude', 'created_at')
    search_fields = ('title', 'message', 'user__username')
    list_filter = ('message_type', 'created_at')