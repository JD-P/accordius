from django.contrib.auth.models import User
from lw2.models import *
from rest_framework import serializers

class UserSerializer(serializers.HyperlinkedModelSerializer):
    model = User
    fields = ('url','username','email')

class TagSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Tag
        fields = ('user','document_id','created_at','type','text')

class BanSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Ban
        fields = ('user', 'created_at', 'reason',
                  'ban_message', 'until', 'appeal_on')
