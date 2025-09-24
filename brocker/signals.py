from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from brocker.models import BrokerPermission, BrokerTokens, BrokerTags
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from brocker.consumers import sanitize_tag
import logging

logger = logging.getLogger(__name__)

def notify_permission_change(instance, permission_level):
    channel_layer = get_channel_layer()
    if channel_layer:
        token = instance.broker.token
        pattern = instance.tag.prefix
        async_to_sync(channel_layer.group_send)(
            f"token_{sanitize_tag(token)}",
            {
                "type": "permission_update",
                "pattern": pattern,
                "permission": permission_level
            }
        )

@receiver(post_save, sender=BrokerPermission)
def permission_updated(sender, instance, created, **kwargs):
    action = "created" if created else "updated"
    logger.info(
        "Permission %s for token '%s' on tag '%s' with level '%s'. Notifying clients.",
        action, instance.broker.token, instance.tag.prefix, instance.permission
    )
    notify_permission_change(instance, instance.permission)

@receiver(post_delete, sender=BrokerPermission)
def permission_deleted(sender, instance, **kwargs):
    logger.info(
        "Permission deleted for token '%s' on tag '%s'. Notifying clients.",
        instance.broker.token, instance.tag.prefix
    )
    notify_permission_change(instance, None)

def notify_token_change(token):
    channel_layer = get_channel_layer()
    if channel_layer:
        logger.info("Notifying clients of token '%s' to disconnect due to modification/deletion.", token)
        async_to_sync(channel_layer.group_send)(
            f"token_{sanitize_tag(token)}",  
            {"type": "token_update"}
        )

@receiver(post_delete, sender=BrokerTokens)
def token_deleted(sender, instance, **kwargs):
    notify_token_change(instance.token)

@receiver(post_save, sender=BrokerTokens)
def token_updated(sender, instance, **kwargs):
    notify_token_change(instance.token)

def notify_tag_change(old_prefix):
    channel_layer = get_channel_layer()
    if channel_layer:
        logger.info("Broadcasting tag pattern modification for '%s' to all clients.", old_prefix)
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
        logger.info("Tag pattern updated from '%s' to '%s'.", old_prefix, instance.prefix)
        notify_tag_change(old_prefix)