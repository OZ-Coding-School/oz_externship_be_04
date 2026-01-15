from rest_framework import serializers

from apps.lectures.models import Category


class CategorySerializer(serializers.ModelSerializer[Category]):
    class Meta:
        model = Category
        fields = ["id", "name"]
        read_only_fields = ["id"]
