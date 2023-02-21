from rest_framework import serializers
from tracking_api.models import BlackListed, Tracking


class TrackingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tracking
        fields = '__all__'


class BlacklistedSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlackListed
        fields = '__all__'


class StatusSerializer(serializers.Serializer):
    status = serializers.CharField()
    date = serializers.DateTimeField()

class TrackingStatusSerializer(serializers.Serializer):
    estimateDelivery = serializers.DateTimeField(required=False)
    status = StatusSerializer(many=True)