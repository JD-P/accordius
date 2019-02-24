from django.contrib.auth.models import User
from lw2.models import *
from rest_framework import serializers
import datetime
import hashlib
import base64
import random

def make_id(username, utc_timestamp):
    hashable = username + str(utc_timestamp)
    hash_raw = hashlib.md5(hashable.encode())
    hash_b64 = base64.b64encode(hash_raw.digest()).decode()
    return hash_b64[:17].replace("/","_").replace("+","-")

def make_id_from_user(username):
    """Wrapper around make_id that eliminates finnicky time handling code."""
    return make_id(username,
                   datetime.datetime.today().replace(tzinfo=datetime.timezone.utc).timestamp())

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

        user_profile = Profile()
        user_profile.user = new_user
        user_profile.save()
        
        return new_user

class PostSerializer(serializers.ModelSerializer):
    _id = serializers.CharField(source="id", read_only=True)
    userId = serializers.CharField(source="user.id", read_only=True)
    postedAt = serializers.DateTimeField(source="posted_at", read_only=True)
    title = serializers.CharField()
    url = serializers.URLField(required=False)
    slug = serializers.CharField(read_only=True)
    baseScore = serializers.IntegerField(source="base_score", read_only=True)
    body = serializers.CharField()
    commentCount = serializers.IntegerField(source="comment_count", read_only=True)
    viewCount = serializers.IntegerField(source="view_count", read_only=True)
    meta = serializers.BooleanField(default=False, read_only=True)
    af = serializers.BooleanField(default=False, read_only=True)
    question = serializers.BooleanField(default=False, read_only=True)
    voteCount = serializers.IntegerField(source="vote_count", read_only=True)
    draft = serializers.BooleanField(default=False, read_only=True)
    class Meta:
        model = Post
        fields = ('_id', 'userId', 'postedAt', 'title',
                  'url', 'slug', 'body', 'baseScore',
                  'voteCount', 'commentCount', 'viewCount', 'meta',
                  'af', 'question', 'draft')

    def validate_title(self, value):
        if not value:
            raise serializers.ValidationError("You must give your post a title.")
        else:
            return value
        
    def create(self, validated_data):
        # We're forced to create the posts manually to generate ID's for them
        # TODO: Comments almost certainly suffer from a similar error, reevaluate
        # need for these ID's
        user = self.context["request"].user
        try:
            url = validated_data.pop("url")
        except:
            url = None
        title = validated_data.pop("title")
        slug = title.strip().lower().replace(" ", "-")[:60]
        new_post = Post(id=make_id_from_user(user.username),
                        user=user,
                        title=title,
                        url=url,
                        slug=slug,
                        body=validated_data.pop("body"))
        new_post.full_clean()
        new_post.save()
        return new_post
        
class CommentSerializer(serializers.ModelSerializer):
    _id = serializers.CharField(source="id", read_only=True)
    userId = serializers.CharField(source="user.id", read_only=True)
    postId = serializers.CharField(source="post.id")
    parentCommentId = serializers.CharField(default=None, source="parent_comment.id")
    postedAt = serializers.DateTimeField(source="posted_at", read_only=True)
    baseScore = serializers.IntegerField(source="base_score", read_only=True)
    body = serializers.CharField()
    retracted = serializers.BooleanField()
    answer = serializers.BooleanField(default=False, read_only=True)
    htmlBody = serializers.CharField(default="", read_only=True)
    isDeleted = serializers.BooleanField(source="is_deleted")
    class Meta:
        model = Comment
        fields = ('_id', 'userId', 'postId', 'parentCommentId',
                  'postedAt', 'baseScore', 'body', 'retracted',
                  'answer', 'htmlBody', 'isDeleted')
    
class TagSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'user','document_id','created_at','type','text')
        read_only_fields = ('id', 'user', 'created_at', 'type')

    def create(self, validated_data):
        user = self.context["request"].user
        document_id = validated_data.pop('document_id')
        try:
            post = Post.objects.filter(id=document_id)[0]
        except IndexError:
            raise ValueError("No post with ID {}".format(document_id))
        #TODO: Use more flexible way of determining this permission
        if (user != post.user) and not user.profile.all()[0].moderator:
            raise ValueError(
                "User '{}' is not authorized to add a tag to this document.".format(
                    user.username
                )
            )
        new_tag = Tag()
        new_tag.user = user
        #TODO: Restrict creation of tags to appropriate character set/etc
        new_tag.text = validated_data.pop('text')
        new_tag.created_at = datetime.datetime.now()
        #TODO: Add ability to tag more than just posts, perhaps comments?
        new_tag.type = "post"
        new_tag.document_id = document_id
        new_tag.full_clean()
        new_tag.save()
        return new_tag

class VoteSerializer(serializers.HyperlinkedModelSerializer):
    collection_name = serializers.CharField(
        write_only=True,
        help_text="The collection to which a document belongs, generally 'posts' or 'comments'.")
    class Meta:
        model = Vote
        fields = ('user', 'document_id', 'voted_at', 'vote_type', 'power',
                  'collection_name')
        read_only_fields = ('user', 'voted_at', 'power')

    # TODO: Stop unauthenticated users from voting on submissions :p
    # TODO: Decide whether we want voting at all, overhaul voting system
    # TODO: Fix bug where you can't change votes
    # TODO: This code looks repetitive and ugly, refactor?
    def create(self, validated_data):
        document_id = validated_data.pop("document_id")
        vote_type = validated_data.pop("vote_type")
        collection_name = validated_data.pop("collection_name")
        if collection_name.lower() == "comments":
            if Vote.objects.filter(document_id=document_id):
                return HttpResponse("User already voted on this",
                                    status_code=409)
            comment = Comment.objects.get(id=document_id)
            #TODO: Enforce valid vote types
            vote = Vote(user=self.context["request"].user,
                        document_id=document_id,
                        voted_at=datetime.datetime.today(),
                        vote_type=vote_type)
            if "Upvote" in vote_type:
                comment.base_score += 1
            elif "Downvote" in vote_type:
                comment.base_score -= 1
            else:
                return HttpResponse(
                    "'{}' does not appear to be upvote or downvote".format(
                        vote_type),
                    status_code=400
                )
            vote.save()
            comment.save()
            return vote
        elif collection_name.lower() == "posts":
            if Vote.objects.filter(document_id=document_id):
                return HttpResponse("User already voted on this",
                                    status_code=409)
            post = Post.objects.get(id=document_id)
            #TODO: Enforce valid vote types
            vote = Vote(user=self.context["request"].user,
                        document_id=document_id,
                        voted_at=datetime.datetime.today(),
                        vote_type=vote_type)
            if "Upvote" in vote_type:
                post.base_score += 1
            elif "Downvote" in vote_type:
                post.base_score -= 1
            else:
                return HttpResponse(
                    "'{}' does not appear to be upvote or downvote".format(
                        vote_type),
                    status_code=400
                )
            vote.save()
            post.save()
            return vote
        else:
            return HttpResponse(
                "Collection '{}' is not handled by accordius!".format(
                    collection_name),
                status_code=400)
        
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
