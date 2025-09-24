from asgiref.sync import sync_to_async
from .MqttPatternMatcher import MqttPatternMatcher

matcher = MqttPatternMatcher()

@sync_to_async
def get_broker_token(token_str):
    from .models import BrokerTokens  
    return BrokerTokens.objects.filter(token=token_str).first()

@sync_to_async
def get_permissions(token_obj):
    from .models import BrokerPermission  
    perms = BrokerPermission.objects.filter(broker=token_obj).select_related('tag')
    return [(p.tag.prefix, p.permission) for p in perms]
