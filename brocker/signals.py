# signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from brocker.models import BrokerPermission, BrokerTokens, BrokerTags
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from brocker.consumers import sanitize_tag
import json

channel_layer = get_channel_layer()

@receiver(post_save, sender=BrokerPermission)
def permission_updated(sender, instance, **kwargs):
    """
    Signal triggered when a BrokerPermission is created or updated.
    Sends update to all WebSocket clients connected with the token.
    """
    token = instance.broker.token
    tag = instance.tag.prefix
    permission = instance.permission

    async_to_sync(channel_layer.group_send)(
        f"token_{sanitize_tag(token)}",  # group per token
        {
            "type": "permission_update",
            "tag": tag,
            "permission": permission
        }
    )

@receiver(post_delete, sender=BrokerPermission)
def permission_deleted(sender, instance, **kwargs):
    """
    Signal triggered when a BrokerPermission is deleted.
    Notifies WebSocket clients to remove the tag from their groups.
    """
    token = instance.broker.token
    tag = instance.tag.prefix

    async_to_sync(channel_layer.group_send)(
        f"token_{sanitize_tag(token)}",
        {
            "type": "permission_update",
            "tag": tag,
            "permission": None  
        }
    )


def notify_disconnect(token):
    async_to_sync(channel_layer.group_send)(
        f"token_{sanitize_tag(token)}",  
        {
            "type": "token_update",
            "new_token": None  
        }
    )

@receiver(post_delete, sender=BrokerTokens)
def token_deleted(sender, instance, **kwargs):
    notify_disconnect(instance.token)

@receiver(post_save, sender=BrokerTokens)
def token_updated(sender, instance, **kwargs):
    notify_disconnect(instance.token)

def notify_tag_change(old_prefix):
    for broker in BrokerTokens.objects.all():
        async_to_sync(channel_layer.group_send)(
            f"token_{sanitize_tag(broker.token)}",
            {
                "type": "tag_update",
                "old_prefix": old_prefix
            }
        )
@receiver(post_delete, sender=BrokerTags)
def tag_deleted(sender, instance, **kwargs):
    notify_tag_change(instance.prefix)

@receiver(post_save, sender=BrokerTags)
def tag_updated(sender, instance, **kwargs):
    old_prefix = getattr(instance, "_old_prefix", None)
    if old_prefix and old_prefix != instance.prefix:
        notify_tag_change(old_prefix)
