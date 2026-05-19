from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

# 4.1 Модуль авторизации - расширенный профиль пользователя
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Телефон")
    city = models.CharField(max_length=255, blank=True, null=True, verbose_name="Город")
    notification_enabled = models.BooleanField(default=True, verbose_name="Уведомления включены")
    nickname = models.CharField(max_length=50, blank=True, null=True, verbose_name="Никнейм")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name="Аватар")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата регистрации")

    def __str__(self):
        return f"Профиль {self.user.username}"

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"


# 4.2 Модуль мониторинга трасс - маршруты
class Route(models.Model):
    name = models.CharField(max_length=255, verbose_name="Имя маршрута")
    start_lat = models.FloatField(verbose_name="Начало - широта")
    start_lng = models.FloatField(verbose_name="Начало - долгота")
    end_lat = models.FloatField(verbose_name="Конец - широта")
    end_lng = models.FloatField(verbose_name="Конец - долгота")
    waypoints = models.JSONField(default=list, verbose_name="Промежуточные точки")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='routes', verbose_name="Пользователь")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Маршрут"
        verbose_name_plural = "Маршруты"


# Основной класс для участков дороги
class Road(models.Model):
    STATUS_CHOICES = [
        ('open', 'Открыта'),
        ('closed', 'Закрыта'),
        ('partially_restricted', 'Частично ограничена'),
    ]
    
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='roads', verbose_name="Маршрут", null=True, blank=True)
    name = models.CharField(max_length=255, verbose_name="Участок дороги")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='open', verbose_name="Состояние")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Оператор")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата замера")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    def __str__(self):
        return f"{self.name} - {self.get_status_display()}"

    class Meta:
        verbose_name = "Участок дороги"
        verbose_name_plural = "Участки дорог"


# 4.3 Модуль мониторинга погоды
class Weather(models.Model):
    road = models.OneToOneField(Road, on_delete=models.CASCADE, related_name='weather', verbose_name="Участок дороги", null=True, blank=True)
    temperature = models.IntegerField(verbose_name="Температура воздуха (°C)")
    precipitation = models.CharField(max_length=50, verbose_name="Осадки")  # дождь, снег, град и т.д.
    wind_speed = models.FloatField(verbose_name="Скорость ветра (км/ч)")
    visibility = models.FloatField(verbose_name="Видимость (м)")  # в метрах
    ice_probability = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Вероятность гололёда (%)"
    )
    mcs_warning = models.CharField(max_length=255, blank=True, null=True, verbose_name="Предупреждение МЧС")
    
    measured_at = models.DateTimeField(auto_now_add=True, verbose_name="Время замера")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    def __str__(self):
        return f"Погода на {self.road.name if self.road else 'Без маршрута'} - {self.temperature}°C"

    class Meta:
        verbose_name = "Данные погоды"
        verbose_name_plural = "Данные погоды"


# Экстренные предупреждения - аварии, ДТП, затруднения
class EmergencyWarning(models.Model):
    WARNING_TYPE_CHOICES = [
        ('accident', 'Авария'),
        ('traffic_delay', 'Затруднение движения'),
        ('weather_hazard', 'Опасность из-за погоды'),
        ('repair_work', 'Ремонтные работы'),
        ('other', 'Прочее'),
    ]
    
    road = models.ForeignKey(Road, on_delete=models.CASCADE, related_name='warnings', verbose_name="Участок дороги", null=True, blank=True)
    warning_type = models.CharField(max_length=50, choices=WARNING_TYPE_CHOICES, verbose_name="Тип предупреждения")
    title = models.CharField(max_length=255, verbose_name="Заголовок")
    description = models.TextField(verbose_name="Описание")
    severity = models.CharField(max_length=50, choices=[('low', 'Низкая'), ('medium', 'Средняя'), ('high', 'Высокая')], verbose_name="Уровень серьезности")
    
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Автор")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата разрешения")

    def __str__(self):
        return f"{self.get_warning_type_display()} - {self.road.name if self.road else 'Без маршрута'}"

    class Meta:
        verbose_name = "Экстренное предупреждение"
        verbose_name_plural = "Экстренные предупреждения"


# Опасные участки
class DangerousArea(models.Model):
    DANGER_TYPE_CHOICES = [
        ('ice', 'Гололёд'),
        ('snow', 'Снег'),
        ('flooding', 'Затопление'),
        ('pothole', 'Яма'),
        ('debris', 'Обломки'),
        ('slippery', 'Скользкая дорога'),
        ('other', 'Прочее'),
    ]
    
    road = models.ForeignKey(Road, on_delete=models.CASCADE, related_name='dangerous_areas', verbose_name="Участок дороги", null=True, blank=True)
    danger_type = models.CharField(max_length=50, choices=DANGER_TYPE_CHOICES, verbose_name="Тип опасности")
    location = models.CharField(max_length=255, verbose_name="Местоположение")
    latitude = models.FloatField(verbose_name="Широта")
    longitude = models.FloatField(verbose_name="Долгота")
    description = models.TextField(verbose_name="Описание")
    
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Автор")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата разрешения")

    def __str__(self):
        return f"{self.get_danger_type_display()} - {self.road.name if self.road else 'Без маршрута'}"

    class Meta:
        verbose_name = "Опасный участок"
        verbose_name_plural = "Опасные участки"


# Пользовательские сообщения на карте
class UserMessage(models.Model):
    MESSAGE_TYPE_CHOICES = [
        ('accident', 'Авария'),
        ('traffic_jam', 'Пробка'),
        ('road_work', 'Дорожные работы'),
        ('weather', 'Погода'),
        ('other', 'Прочее'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages', verbose_name="Пользователь")
    latitude = models.FloatField(verbose_name="Широта")
    longitude = models.FloatField(verbose_name="Долгота")
    message_type = models.CharField(max_length=50, choices=MESSAGE_TYPE_CHOICES, verbose_name="Тип сообщения")
    title = models.CharField(max_length=255, verbose_name="Заголовок")
    message = models.TextField(verbose_name="Сообщение")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    def __str__(self):
        return f"{self.get_message_type_display()} - {self.user.username}"

    class Meta:
        verbose_name = "Сообщение пользователя"
        verbose_name_plural = "Сообщения пользователей"


class UserMessageReaction(models.Model):
    message = models.ForeignKey(UserMessage, on_delete=models.CASCADE, related_name='reactions', verbose_name='Сообщение')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='message_reactions', verbose_name='Пользователь')
    is_like = models.BooleanField(verbose_name='Лайк')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        unique_together = ('message', 'user')
        verbose_name = 'Реакция на сообщение'
        verbose_name_plural = 'Реакции на сообщения'

    def __str__(self):
        return f"{self.user.username} {'лайкнул' if self.is_like else 'дизлайкнул'} {self.message.title}"


class UserMessageComment(models.Model):
    message = models.ForeignKey(UserMessage, on_delete=models.CASCADE, related_name='comments', verbose_name='Сообщение')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='message_comments', verbose_name='Пользователь')
    text = models.TextField(verbose_name='Текст комментария')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies', verbose_name='Ответ на')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Комментарий к сообщению'
        verbose_name_plural = 'Комментарии к сообщениям'

    def __str__(self):
        return f"Комментарий {self.user.username} на {self.message.title}"


# 4.5 Модуль уведомлений
class Notification(models.Model):
    NOTIFICATION_TYPE_CHOICES = [
        ('road_closure', 'Перекрытие трассы'),
        ('weather_warning', 'Предупреждение о плохой погоде'),
        ('emergency', 'Аварийное сообщение'),
        ('repair_work', 'Ремонтные работы'),
        ('other', 'Прочее'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', verbose_name="Пользователь")
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPE_CHOICES, verbose_name="Тип уведомления")
    title = models.CharField(max_length=255, verbose_name="Заголовок")
    message = models.TextField(verbose_name="Сообщение")
    related_road = models.ForeignKey(Road, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Связанная дорога")
    
    is_read = models.BooleanField(default=False, verbose_name="Прочитано")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    read_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата прочтения")

    def __str__(self):
        return f"{self.title} - {self.user.username}"

    class Meta:
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"
        ordering = ['-created_at']


@receiver(pre_save, sender=Road)
def notify_road_status_change(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        old = Road.objects.get(pk=instance.pk)
    except Road.DoesNotExist:
        return

    if old.status != instance.status and instance.status in ['closed', 'partially_restricted']:
        notification_type = 'road_closure' if instance.status == 'closed' else 'weather_warning'
        message = f'Участок {instance.name} изменил состояние на {instance.get_status_display()}.'
        for user in User.objects.all():
            Notification.objects.create(
                user=user,
                notification_type=notification_type,
                title='Изменение статуса дороги',
                message=message,
                related_road=instance
            )


@receiver(post_save, sender=Weather)
def notify_weather_hazard(sender, instance, created, **kwargs):
    if instance.ice_probability >= 50 or (instance.mcs_warning or '').strip():
        message = instance.mcs_warning or f'Высокая вероятность гололеда на участке {instance.road.name}.'
        for user in User.objects.all():
            Notification.objects.create(
                user=user,
                notification_type='weather_warning',
                title='Погодное предупреждение',
                message=message,
                related_road=instance.road
            )


@receiver(post_save, sender=EmergencyWarning)
def create_emergency_notification(sender, instance, created, **kwargs):
    if not created:
        return
    notification_type = 'emergency' if instance.warning_type == 'accident' else 'weather_warning' if instance.warning_type == 'weather_hazard' else 'road_closure' if instance.warning_type == 'repair_work' else 'other'
    for user in User.objects.all():
        Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=instance.title,
            message=instance.description,
            related_road=instance.road
        )
