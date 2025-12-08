from typing import Any

from rest_framework import serializers


class ChatroomDetailMemberSerializer(serializers.Serializer[Any]):
    nickname = serializers.CharField(read_only=True)
    is_leader = serializers.BooleanField(read_only=True)


class ChatroomDetailSerializer(serializers.Serializer[Any]):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    members = ChatroomDetailMemberSerializer(many=True, read_only=True)
