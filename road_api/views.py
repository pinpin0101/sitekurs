import requests
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Road, Weather, EmergencyWarning, DangerousArea, Notification, Route, UserProfile, UserMessage, UserMessageReaction, UserMessageComment
from .serializers import (
    RoadSerializer, WeatherSerializer, EmergencyWarningSerializer, 
    DangerousAreaSerializer, NotificationSerializer, RouteSerializer,
    UserSerializer, CurrentUserSerializer, UserRegistrationSerializer, UserProfileSerializer, UserMessageSerializer,
    UserMessageReactionSerializer, UserMessageCommentSerializer
)
from django.conf import settings
from django.shortcuts import render, redirect


def logout_view(request):
    auth_logout(request)
    return redirect('/')


# 4.1 Модуль авторизации - Registration & Login
class UserRegistrationViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=['post'])
    def register(self, request):
        """Регистрация нового пользователя"""
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'user': UserSerializer(user).data,
                'token': token.key,
                'message': 'Пользователь успешно зарегистрирован'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def login(self, request):
        """Вход в систему"""
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response({'error': 'Укажите username и password'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'error': 'Неверные учетные данные'}, status=status.HTTP_401_UNAUTHORIZED)
        
        if not user.check_password(password):
            return Response({'error': 'Неверные учетные данные'}, status=status.HTTP_401_UNAUTHORIZED)
        
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'user': UserSerializer(user).data,
            'token': token.key,
            'message': 'Успешный вход'
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def logout(self, request):
        """Выход из системы"""
        Token.objects.filter(user=request.user).delete()
        return Response({'message': 'Успешный выход'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def password_reset(self, request):
        """Восстановление пароля"""
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Укажите email'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
            # TODO: Реализовать отправку письма с ссылкой восстановления
            return Response({'message': 'Письмо для восстановления пароля отправлено на ваш email'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'Пользователь с таким email не найден'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def profile(self, request):
        """Получение профиля текущего пользователя"""
        user = request.user
        try:
            profile = user.profile
            return Response(UserProfileSerializer(profile).data, status=status.HTTP_200_OK)
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(user=user)
            return Response(UserProfileSerializer(profile).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['put'], permission_classes=[permissions.IsAuthenticated])
    def update_profile(self, request):
        """Обновление профиля текущего пользователя"""
        user = request.user
        try:
            profile = user.profile
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(user=user)
        
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 4.2 Модуль мониторинга трасс - Routes и Roads
class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = Route.objects.all()
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset


@method_decorator(csrf_exempt, name='dispatch')
class RoadViewSet(viewsets.ModelViewSet):
    queryset = Road.objects.all().order_by('-created_at')
    serializer_class = RoadSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = None

    def get_permissions(self):
        # Просмотр доступен всем, а управление (POST, PUT, DELETE) - только авторизованным
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        queryset = Road.objects.all()
        status_filter = self.request.query_params.get('status')
        route_id = self.request.query_params.get('route_id')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if route_id:
            queryset = queryset.filter(route_id=route_id)
        
        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        route = None
        if not self.request.data.get('route'):
            route, _ = Route.objects.get_or_create(
                name='Основной маршрут',
                defaults={
                    'start_lat': 0.0,
                    'start_lng': 0.0,
                    'end_lat': 0.0,
                    'end_lng': 0.0,
                    'waypoints': [],
                    'user': self.request.user
                }
            )
            serializer.save(author=self.request.user, route=route)
        else:
            serializer.save(author=self.request.user)

    @action(detail=True, methods=['get'])
    def by_status(self, request, pk=None):
        """Получить дороги по статусу"""
        roads = Road.objects.filter(status=pk).order_by('-created_at')
        serializer = self.get_serializer(roads, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def critical_areas(self, request):
        """Получить критические участки (закрытые и ограниченные дороги)"""
        roads = Road.objects.filter(status__in=['closed', 'partially_restricted'])
        serializer = self.get_serializer(roads, many=True)
        return Response(serializer.data)


# 4.3 Модуль мониторинга погоды
class WeatherViewSet(viewsets.ModelViewSet):
    queryset = Weather.objects.all()
    serializer_class = WeatherSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = Weather.objects.all()
        road_id = self.request.query_params.get('road_id')
        if road_id:
            queryset = queryset.filter(road_id=road_id)
        return queryset.order_by('-measured_at')

    @action(detail=False, methods=['get'])
    def hazardous_conditions(self, request):
        """Получить дороги с опасными погодными условиями"""
        hazards = Weather.objects.filter(ice_probability__gte=50) | Weather.objects.filter(wind_speed__gte=20)
        serializer = self.get_serializer(hazards, many=True)
        return Response(serializer.data)


# Экстренные предупреждения
class EmergencyWarningViewSet(viewsets.ModelViewSet):
    queryset = EmergencyWarning.objects.all()
    serializer_class = EmergencyWarningSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = None

    def get_queryset(self):
        queryset = EmergencyWarning.objects.all()
        road_id = self.request.query_params.get('road_id')
        warning_type = self.request.query_params.get('warning_type')
        unresolved_only = self.request.query_params.get('unresolved_only', 'false').lower() == 'true'
        
        if road_id:
            queryset = queryset.filter(road_id=road_id)
        if warning_type:
            queryset = queryset.filter(warning_type=warning_type)
        if unresolved_only:
            queryset = queryset.filter(resolved_at__isnull=True)
        
        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Отметить предупреждение как разрешенное"""
        warning = self.get_object()
        warning.resolved_at = timezone.now()
        warning.save()
        return Response({'message': 'Предупреждение отмечено как разрешенное'})

    @action(detail=False, methods=['get'])
    def active_warnings(self, request):
        """Получить активные предупреждения"""
        warnings = EmergencyWarning.objects.filter(resolved_at__isnull=True).order_by('-severity', '-created_at')
        serializer = self.get_serializer(warnings, many=True)
        return Response(serializer.data)


# Опасные участки
class DangerousAreaViewSet(viewsets.ModelViewSet):
    queryset = DangerousArea.objects.all()
    serializer_class = DangerousAreaSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = None

    def get_queryset(self):
        queryset = DangerousArea.objects.all()
        road_id = self.request.query_params.get('road_id')
        danger_type = self.request.query_params.get('danger_type')
        unresolved_only = self.request.query_params.get('unresolved_only', 'false').lower() == 'true'
        
        if road_id:
            queryset = queryset.filter(road_id=road_id)
        if danger_type:
            queryset = queryset.filter(danger_type=danger_type)
        if unresolved_only:
            queryset = queryset.filter(resolved_at__isnull=True)
        
        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Отметить опасный участок как разрешенный"""
        area = self.get_object()
        area.resolved_at = timezone.now()
        area.save()
        return Response({'message': 'Опасный участок отмечен как разрешенный'})


# 4.5 Модуль уведомлений
class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')

    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Получить непрочитанные уведомления"""
        notifications = Notification.objects.filter(user=request.user, is_read=False)
        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Отметить уведомление как прочитанное"""
        notification = self.get_object()
        if notification.user != request.user:
            return Response({'error': 'Нет доступа'}, status=status.HTTP_403_FORBIDDEN)
        
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
        return Response(NotificationSerializer(notification).data)

    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """Отметить все уведомления как прочитанные"""
        Notification.objects.filter(user=request.user, is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        return Response({'message': 'Все уведомления отмечены как прочитанные'})

    @action(detail=False, methods=['get'])
    def count(self, request):
        """Получить количество непрочитанных уведомлений"""
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({'unread_count': count})


# Сообщения пользователей на карте
class UserMessageViewSet(viewsets.ModelViewSet):
    queryset = UserMessage.objects.all().order_by('-created_at')
    serializer_class = UserMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = UserMessage.objects.all().order_by('-created_at')
        if self.request.query_params.get('mine') == 'true':
            queryset = queryset.filter(user=self.request.user)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        message = self.get_object()
        if message.user != request.user:
            return Response({'detail': 'Нельзя удалить чужое сообщение'}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)


class UserMessageReactionViewSet(viewsets.ModelViewSet):
    queryset = UserMessageReaction.objects.all().order_by('-created_at')
    serializer_class = UserMessageReactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = UserMessageReaction.objects.all().order_by('-created_at')
        message_id = self.request.query_params.get('message')
        if message_id:
            queryset = queryset.filter(message_id=message_id)
        return queryset

    def create(self, request, *args, **kwargs):
        message_id = request.data.get('message')
        is_like = request.data.get('is_like')
        if message_id is None or is_like is None:
            return Response({'detail': 'Требуется message и is_like'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            message = UserMessage.objects.get(pk=message_id)
        except UserMessage.DoesNotExist:
            return Response({'detail': 'Сообщение не найдено'}, status=status.HTTP_404_NOT_FOUND)

        try:
            existing = UserMessageReaction.objects.get(message=message, user=request.user)
            if existing.is_like == bool(is_like):
                existing.delete()
                return Response({'detail': 'Реакция удалена'}, status=status.HTTP_204_NO_CONTENT)
            existing.is_like = bool(is_like)
            existing.save()
            reaction = existing
            created = False
        except UserMessageReaction.DoesNotExist:
            reaction = UserMessageReaction.objects.create(
                message=message,
                user=request.user,
                is_like=bool(is_like)
            )
            created = True

        if message.user != request.user:
            Notification.objects.create(
                user=message.user,
                notification_type='other',
                title='Новое взаимодействие с вашим сообщением',
                message=f'{request.user.username} {"лайкнул" if reaction.is_like else "дизлайкнул"} ваше сообщение «{message.title}»'
            )

        serializer = self.get_serializer(reaction)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class UserMessageCommentViewSet(viewsets.ModelViewSet):
    queryset = UserMessageComment.objects.all().order_by('created_at')
    serializer_class = UserMessageCommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = UserMessageComment.objects.all().order_by('created_at')
        message_id = self.request.query_params.get('message')
        if message_id:
            queryset = queryset.filter(message_id=message_id)
        return queryset

    def create(self, request, *args, **kwargs):
        message_id = request.data.get('message')
        text = request.data.get('text')
        parent_id = request.data.get('parent')

        if not message_id or not text:
            return Response({'detail': 'Требуется message и text'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            message = UserMessage.objects.get(pk=message_id)
        except UserMessage.DoesNotExist:
            return Response({'detail': 'Сообщение не найдено'}, status=status.HTTP_404_NOT_FOUND)

        parent = None
        if parent_id:
            try:
                parent = UserMessageComment.objects.get(pk=parent_id)
            except UserMessageComment.DoesNotExist:
                return Response({'detail': 'Родительский комментарий не найден'}, status=status.HTTP_404_NOT_FOUND)

        comment = UserMessageComment.objects.create(
            message=message,
            user=request.user,
            text=text,
            parent=parent
        )

        if message.user != request.user:
            Notification.objects.create(
                user=message.user,
                notification_type='other',
                title='Новый комментарий к вашему сообщению',
                message=f'{request.user.username} прокомментировал ваше сообщение «{message.title}»'
            )

        serializer = self.get_serializer(comment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        if comment.user != request.user and comment.message.user != request.user:
            return Response({'detail': 'Нельзя удалить этот комментарий'}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)


def index(request):
    return render(request, 'index.html', {
        'TWO_GIS_TILE_URL': getattr(settings, 'TWO_GIS_TILE_URL', ''),
        'TWO_GIS_API_KEY': getattr(settings, 'TWO_GIS_API_KEY', ''),
    })


def road_status_view(request):
    return render(request, 'road_status.html')


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def current_user_view(request):
    if request.user.is_authenticated:
        try:
            profile = request.user.profile
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(user=request.user)
        return Response(CurrentUserSerializer(request.user).data)
    return Response({'is_anonymous': True})


def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect('profile')
    else:
        form = UserCreationForm()

    return render(request, 'registration/register.html', {'form': form})


@login_required
def profile_view(request):
    if request.method == 'POST':
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        profile.nickname = request.POST.get('nickname', '').strip() or None
        profile.phone = request.POST.get('phone', '').strip() or None
        profile.city = request.POST.get('city', '').strip() or None
        if 'avatar' in request.FILES:
            profile.avatar = request.FILES['avatar']
        profile.save()
        messages.success(request, 'Профиль обновлен успешно!')
        return redirect('profile')
    return render(request, 'profile.html', {'user': request.user})