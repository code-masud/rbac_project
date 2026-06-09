from rest_framework import serializers
from .models import Comment
from apps.accounts.serializers import UserSerializer


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for Comment model"""
    
    author_name = serializers.SerializerMethodField()
    author_role = serializers.SerializerMethodField()
    post_title = serializers.ReadOnlyField(source='post.title')
    
    class Meta:
        model = Comment
        fields = ('id', 'content', 'post', 'post_title', 'author', 'author_name', 
                 'author_role', 'created_at', 'updated_at', 'is_active')
        read_only_fields = ('id', 'author', 'created_at', 'updated_at', 
                           'author_name', 'author_role', 'post_title', 'is_active')
    
    def get_author_name(self, obj):
        return f"{obj.author.first_name} {obj.author.last_name}" if obj.author.first_name else obj.author.email
    
    def get_author_role(self, obj):
        return obj.author.role
    
    def validate_content(self, value):
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Comment content cannot be empty")
        if len(value) > 1000:
            raise serializers.ValidationError("Comment must be less than 1000 characters")
        return value


class CommentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating comments"""
    
    class Meta:
        model = Comment
        fields = ('content', 'post')
    
    def validate_post(self, value):
        if not value.is_active:
            raise serializers.ValidationError("Cannot comment on inactive posts")
        return value
    
    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)