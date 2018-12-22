from django.contrib.auth.models import User
from lw2.models import *
from rest_framework import serializers
import datetime
import random

class UserSerializer(serializers.HyperlinkedModelSerializer):
    code = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        #TODO: Conditionally display a users email address if they choose to make it public
        fields = ('username', 'password', 'email', 'code')

    def create(self, validated_data):
        invite_code = validated_data.pop('code')
        try:
            invite = Invite.objects.filter(code=invite_code)[0]
        except IndexError:
            raise ValueError("No invite with that code in our database.")
        tzinfo = datetime.timezone(-datetime.timedelta(hours=8))
        if invite.expires < datetime.datetime.now(tz=tzinfo):
            raise ValueError("This invite has expired.")
        if invite.used_by:
            raise ValueError("This invite has been used.")
        #TODO: Filter out characters which aren't ascii, or something
        #TODO: Force users not to use stupid weak passwords
        new_user = User.objects.create_user(validated_data.pop('username'),
                                            password=validated_data.pop('password'),
                                            email=validated_data.pop('email'))

        invite.used_date = datetime.datetime.now()
        invite.used_by = new_user
        invite.save()

        invite_tree_node = InviteTreeNode()
        invite_tree_node.parent = invite.creator
        invite_tree_node.child = new_user
        invite_tree_node.save()

        return new_user
        
class TagSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Tag
        fields = ('user','document_id','created_at','type','text')

class BanSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Ban
        fields = ('user', 'created_at', 'reason',
                  'ban_message', 'until', 'appeal_on')

class InviteSerializer(serializers.HyperlinkedModelSerializer):
    expires = serializers.DateTimeField(required=False)
    
    class Meta:
        model = Invite
        fields = ('id', 'creator', 'date_created', 'used_date', 'used_by', 'expires',)
        read_only_fields = ('id', 'creator', 'date_created', 'used_date', 'used_by')
        
    def create(self, validated_data):
        #TODO: Limit how many invites a user can make based on a configuration option
        user = self.context["request"].user
        try:
            expires = validated_data.pop('expires')
        except KeyError:
            expires = None
        invite = Invite()
        if not user.is_authenticated:
            raise ValueError("This user is not authenticated with services.")
        invite.creator = user
        rng = random.SystemRandom()
        invite.code = str(rng.getrandbits(64))
        invite.date_created = datetime.datetime.now()
        if user.profile.all()[0].moderator and expires:
            invite.expires = expires
        else:
            invite.expires = datetime.datetime.now() + datetime.timedelta(weeks=+9)
        invite.save()
        return invite

class RestrictedInviteSerializer(serializers.HyperlinkedModelSerializer):
    """Invite serializer which returns the actual invite codes in addition to 
    other information. Because the invite codes could be used to sign up for the 
    website, they should only be shown to the user that created an invitation or
    site administrators."""
    class Meta:
        model = Invite
        fields = ('id', 'creator', 'code', 'date_created', 'used_date', 'used_by', 'expires')
        read_only_fields = ('id', 'creator', 'code', 'date_created', 'used_date', 'used_by', 'expires')
