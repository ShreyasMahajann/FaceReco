# api/serializers.py

from rest_framework import serializers

class VerificationSerializer(serializers.Serializer):
    roll = serializers.IntegerField()
    image = serializers.CharField()
