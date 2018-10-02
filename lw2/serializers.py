from django.contrib.auth.models import User
from lw2.models import Tag
from rest_framework import serializers

class UserSerializer(serializers.HyperlinkedModelSerializer):
    model = User
    fields = ('url','username','email')

class TagSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Tag
        fields = ('user','document_id','created_at','type','text')

