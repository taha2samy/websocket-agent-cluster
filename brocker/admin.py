from django.contrib import admin
from .models import BrokerTokens, BrokerPermission, BrokerTags

@admin.register(BrokerTokens)
class BrokerTokensAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'token', 'max_connections')
    search_fields = ('name', 'token')
    list_per_page = 20

@admin.register(BrokerPermission)
class BrokerPermissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'broker', 'tag', 'permission')  
    list_filter = ('permission',)
    search_fields = ('broker__token', 'tag__prefix')  
    list_per_page = 20

@admin.register(BrokerTags)
class BrokerTagsAdmin(admin.ModelAdmin):
    list_display = ('id', 'prefix')
    search_fields = ('prefix',)
    list_per_page = 20
