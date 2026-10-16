from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """Read-only representation of a notification for its recipient."""

    is_read = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id",
            "type",
            "title",
            "message",
            "related_object_type",
            "related_object_id",
            "is_read",
            "created_at",
            "read_at",
        ]
        read_only_fields = fields

    def get_is_read(self, notification):
        return notification.read_at is not None
