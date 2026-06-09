from rest_framework import serializers
from .models import Post
from accounts.serializers import UserSerializer


class PostSerializer(serializers.ModelSerializer):
    """Serializer for Post model"""
    
    author_name = serializers.SerializerMethodField()
    comment_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Post
        fields = ('id', 'title', 'content', 'author', 'author_name', 
                 'comment_count', 'created_at', 'updated_at', 'is_active')
        read_only_fields = ('id', 'author', 'created_at', 'updated_at', 
                           'comment_count', 'author_name', 'is_active')
    
    def get_author_name(self, obj):
        return f"{obj.author.first_name} {obj.author.last_name}" if obj.author.first_name else obj.author.email
    
    def validate_title(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("Title must be at least 3 characters long")
        if len(value) > 200:
            raise serializers.ValidationError("Title must be less than 200 characters")
        return value
    
    def validate_content(self, value):
        if len(value) < 10:
            raise serializers.ValidationError("Content must be at least 10 characters long")
        return value


class PostCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating posts"""
    
    class Meta:
        model = Post
        fields = ('title', 'content')
    
    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)