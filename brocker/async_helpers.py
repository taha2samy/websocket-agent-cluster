from asgiref.sync import sync_to_async
from brocker.MqttPatternMatcher import MqttPatternMatcher
import logging

logger = logging.getLogger(__name__)
matcher = MqttPatternMatcher()

@sync_to_async
def get_broker_token(token_str):
    from .models import BrokerTokens
    logger.debug("Querying database for token: %s", token_str)
    token_obj = BrokerTokens.objects.filter(token=token_str).first()
    if token_obj:
        logger.debug("Token found for: %s", token_str)
    else:
        logger.debug("Token not found for: %s", token_str)
    return token_obj

@sync_to_async
def get_permissions(token_obj):
    from .models import BrokerPermission
    logger.debug("Querying permissions for token ID: %s", token_obj.id)
    perms = BrokerPermission.objects.filter(broker=token_obj).select_related('tag')
    permissions_list = [(p.tag.prefix, p.permission) for p in perms]
    logger.debug("Found %d permissions for token ID: %s", len(permissions_list), token_obj.id)
    return permissions_list