# game/signals.py

from django.db.models.signals import post_save
from django.contrib.auth.signals import user_logged_in
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Profile
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

# Quando um usuário faz login, enviamos uma mensagem para o grupo de presença.
@receiver(user_logged_in)
def user_logged_in_handler(sender, request, user, **kwargs):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'presence',
        {
            # O tipo da mensagem precisa corresponder a um método no consumer.
            # Vamos criar um método simples para lidar com isso.
            'type': 'user_joined', 
        }
    )