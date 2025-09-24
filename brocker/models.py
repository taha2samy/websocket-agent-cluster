from django.db import models
from brocker.MqttPatternMatcher import MqttPatternMatcher
from django.core.exceptions import ValidationError
# Create your models here.
class BrokerTokens(models.Model):
    name = models.CharField(max_length=255,null=True, blank=True)
    token = models.TextField(unique=True)
    max_connections = models.IntegerField(default=0)  # 0 for unlimited
    def __str__(self):
        return self.name if self.name else self.token
class BrokerPermission(models.Model):
    PERMISSION_CHOICES = [
        ('read', 'Read'),
        ('readwrite', 'ReadWrite'),
    ]
    broker = models.ForeignKey(BrokerTokens, on_delete=models.CASCADE)
    tag = models.ForeignKey('BrokerTags', on_delete=models.CASCADE)
    permission = models.CharField(max_length=11, choices=PERMISSION_CHOICES)

    def __str__(self):
        return f"{self.broker} - {self.tag} ({self.permission})"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['broker', 'tag'], name='unique_broker_tag')
        ]

    def save(self, *args, **kwargs):
        if self.pk:
            old = BrokerPermission.objects.get(pk=self.pk)
            if old.broker != self.broker or old.tag != self.tag:
                old.delete()
                self.pk = None
        super().save(*args, **kwargs)


class BrokerTags(models.Model):
    prefix = models.TextField(unique=True)

    def __str__(self):
        return self.prefix

    def save(self, *args, **kwargs):
        if self.pk:
            old = BrokerTags.objects.get(pk=self.pk)
            old_prefix = old.prefix
            if old_prefix != self.prefix:
                old.delete()
        super().save(*args, **kwargs)


    def clean(self):
        """
        Ensure that the new prefix does not conflict or overlap with existing prefixes,
        using MQTT pattern matching with wildcards.
        """
        matcher = MqttPatternMatcher()
        existing_prefixes = BrokerTags.objects.exclude(id=self.id).values_list('prefix', flat=True)

        for ep in existing_prefixes:
            if matcher.is_match(self.prefix, [ep])["match"] or matcher.is_match(ep, [self.prefix])["match"]:
                raise ValidationError(f"Prefix '{self.prefix}' conflicts or overlaps with existing prefix '{ep}'")

    def save(self, *args, **kwargs):
        self.full_clean()  # This will call clean() before saving
        super().save(*args, **kwargs)
