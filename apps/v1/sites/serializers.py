from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from .models import Contact, Partner, Request


class ContactSerializer(serializers.ModelSerializer):
    """Serializer for Contact"""
    full_address = serializers.SerializerMethodField()
    
    class Meta:
        model = Contact
        fields = (
            'id', 'zip_code', 'city', 'street', 'building_number', 'office_number',
            'phone', 'email', 'working_hours_weekday', 'working_hours_weekend',
            'map_iframe', 'full_address', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')
    
    def get_full_address(self, obj):
        """Get full address"""
        return obj.get_full_address()


class PartnerSerializer(serializers.ModelSerializer):
    """Serializer for Partner"""
    image = serializers.ImageField(use_url=True)
    
    class Meta:
        model = Partner
        fields = ('id', 'image', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')


class RequestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating requests"""
    file = serializers.FileField(required=False, allow_null=True)
    
    class Meta:
        model = Request
        fields = ('name', 'phone', 'email', 'comment', 'file', 'privacy_policy_agreed')
        extra_kwargs = {
            'file': {'help_text': 'Прикрепленный файл'}
        }
    
    def validate_privacy_policy_agreed(self, value):
        """Validate privacy policy agreement"""
        if not value:
            raise serializers.ValidationError("Необходимо согласие с политикой конфиденциальности")
        return value
