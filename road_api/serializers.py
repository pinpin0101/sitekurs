from rest_framework import serializers
from .models import Road, Weather, EmergencyWarning, DangerousArea, Notification, Route, UserProfile, UserMessage, UserMessageReaction, UserMessageComment
from django.contrib.auth.models import User


class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source='user.username')
    email = serializers.ReadOnlyField(source='user.email')
    
    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'email', 'phone', 'city', 'notification_enabled', 'nickname', 'avatar', 'created_at']


class CurrentUserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profile']


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ['id', 'name', 'start_lat', 'start_lng', 'end_lat', 'end_lng', 'waypoints', 'created_at', 'user']


class WeatherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Weather
        fields = ['id', 'road', 'temperature', 'precipitation', 'wind_speed', 'visibility', 'ice_probability', 'mcs_warning', 'measured_at', 'updated_at']


class EmergencyWarningSerializer(serializers.ModelSerializer):
    author_name = serializers.ReadOnlyField(source='author.username')
    
    class Meta:
        model = EmergencyWarning
        fields = ['id', 'road', 'warning_type', 'title', 'description', 'severity', 'author', 'author_name', 'created_at', 'resolved_at']


class DangerousAreaSerializer(serializers.ModelSerializer):
    author_name = serializers.ReadOnlyField(source='author.username')
    
    class Meta:
        model = DangerousArea
        fields = ['id', 'road', 'danger_type', 'location', 'latitude', 'longitude', 'description', 'author', 'author_name', 'created_at', 'resolved_at']


class NotificationSerializer(serializers.ModelSerializer):
    related_road_name = serializers.ReadOnlyField(source='related_road.name')
    related_road_id = serializers.ReadOnlyField(source='related_road.id')

    class Meta:
        model = Notification
        fields = ['id', 'notification_type', 'title', 'message', 'related_road', 'related_road_name', 'related_road_id', 'is_read', 'created_at', 'read_at']


class UserMessageSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    user_name = serializers.ReadOnlyField(source='user.username')
    message_type_display = serializers.ReadOnlyField(source='get_message_type_display')
    
    class Meta:
        model = UserMessage
        fields = ['id', 'user', 'user_name', 'latitude', 'longitude', 'message_type', 'message_type_display', 'title', 'message', 'created_at']


class UserMessageReactionSerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = UserMessageReaction
        fields = ['id', 'message', 'user', 'user_name', 'is_like', 'created_at']
        read_only_fields = ['user', 'user_name', 'created_at']


class UserMessageCommentSerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source='user.username')
    replies = serializers.SerializerMethodField()

    class Meta:
        model = UserMessageComment
        fields = ['id', 'message', 'user', 'user_name', 'text', 'parent', 'replies', 'created_at']
        read_only_fields = ['user', 'user_name', 'replies', 'created_at']

    def get_replies(self, obj):
        return UserMessageCommentSerializer(obj.replies.all(), many=True).data


class RoadSerializer(serializers.ModelSerializer):
    # Добавляем имя автора в ответ, чтобы на фронте было видно, кто сохранил
    author_name = serializers.ReadOnlyField(source='author.username')
    route_name = serializers.ReadOnlyField(source='route.name')
    route_info = RouteSerializer(source='route', read_only=True)
    weather = WeatherSerializer(required=False)
    warnings = EmergencyWarningSerializer(many=True, read_only=True)
    dangerous_areas = DangerousAreaSerializer(many=True, read_only=True)

    class Meta:
        model = Road
        fields = ['id', 'route', 'route_name', 'route_info', 'name', 'status', 'description', 'author', 'author_name', 'weather', 'warnings', 'dangerous_areas', 'created_at', 'updated_at']

    def create(self, validated_data):
        weather_data = validated_data.pop('weather', None)
        route = validated_data.pop('route', None)
        road = Road.objects.create(**validated_data, route=route)
        if weather_data:
            Weather.objects.create(road=road, **weather_data)
        return road

    def update(self, instance, validated_data):
        weather_data = validated_data.pop('weather', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if weather_data:
            Weather.objects.update_or_create(road=instance, defaults=weather_data)
        return instance


# Сериализаторы для регистрации и входа
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'first_name', 'last_name']

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password": "Пароли не совпадают"})
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        UserProfile.objects.create(user=user)
        return user