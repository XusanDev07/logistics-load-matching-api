from rest_framework import serializers
from apps.loads.models import Load


class LoadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Load
        exclude = ('created_at', 'updated_at')
