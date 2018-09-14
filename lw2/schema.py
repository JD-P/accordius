from graphene_django import DjangoObjectType
import graphene
from graphene.types.generic import GenericScalar
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from .models import Profile, Post, Comment, Vote
from datetime import datetime, timezone
import hashlib
import base64
import pdb

def make_id(username, utc_timestamp):
    hashable = username + str(utc_timestamp)
    hash_raw = hashlib.md5(hashable.encode())
    hash_b64 = base64.b64encode(hash_raw.digest()).decode()
    return hash_b64[:17]
    
class UserType(DjangoObjectType):
    class Meta:
        model = User
    slug = graphene.String()
    display_name = graphene.String()

    
    def resolve_slug(self, info):
        return self.username

    def resolve_display_name(self, info):
        try:
            display_name = self.profile_set.all()[0].display_name
        except IndexError:
            print("User {} has no profile!".format(self.username))
            display_name = self.username
        if display_name:
            return display_name
        else:
            return self.username

class VoteType(DjangoObjectType):
    class Meta:
        model = Vote

class CommentType(DjangoObjectType):
    class Meta:
        model = Comment
    _id = graphene.String(name="_id")
    user_id = graphene.String()
    post_id = graphene.String()
    parent_comment_id = graphene.String()
    page_url = graphene.String(default_value="")
    all_votes = graphene.List(VoteType, resolver=lambda x,y: [])
    html_body = graphene.String(default_value="Test comment")
    
    def resolve__id(self, info):
        return self.id
    
    def resolve_user_id(self, info):
        return str(self.user.id)

    def resolve_post_id(self, info):
        return self.post.id

    def resolve_parent_comment_id(self, info):
        return self.parent_comment.id

class CommentsInput(graphene.InputObjectType):
    body = graphene.String()
    post_id = graphene.String()
    parent_comment_id = graphene.String()
    
class CommentsNew(graphene.Mutation):
    class Arguments:
        document = CommentsInput()

    comment = graphene.Field(CommentType)
    _id = graphene.String()

    def resolve__id(self, info):
        return self.comment.id
    
    @staticmethod
    def mutate(root, info, document=None):
        if not document:
            return
        
        if document.parent_comment_id:
            parent_comment =  Comment.objects.get(id=document.parent_comment_id)
        else:
            parent_comment = None
            
        post = Post.objects.get(id=document.post_id)

        user = info.context.user

        posted_at = datetime.today()

        _id = make_id(user.username,
                      posted_at.replace(tzinfo=timezone.utc).timestamp())
        
        comment = Comment(
            id = _id,
            user = user,
            post = post,
            parent_comment = parent_comment,
            posted_at = posted_at,
            body=document.body)
        #TODO: Am I supposed to call save here or is there framework stuff I'm missing?
        comment.save()

        return CommentsNew(comment=comment)

class CommentsEdit(graphene.Mutation):
    class Arguments:
        document_id = graphene.String()
        set = CommentsInput()

    _id = graphene.String(name="_id")
    comment = graphene.Field(CommentType)
    document_id = graphene.String()

    def resolve__id(self, info):
        return self.comment.id
    
    @staticmethod
    def mutate(root, info, document_id=None, set=None):
        pdb.set_trace()
        if not set:
            return None
        comment = Comment.objects.get(id=document_id)
        if info.context.user != comment.user:
            return None
        comment.body = set.body
        comment.save()
        return CommentsEdit(comment=comment)
    
class PostType(DjangoObjectType):
    class Meta:
        model = Post
    _id = graphene.String(name="_id")
    user_id = graphene.String()
    page_url = graphene.String(default_value="")
    word_count = graphene.Int(default_value=1)
    all_votes = graphene.List(VoteType, resolver=lambda x,y: [])

    def resolve__id(self,info):
        return self.id
    
    def resolve_user_id(self, info):
        return str(self.user.id)
    
class PostsInput(graphene.InputObjectType):
    title = graphene.String()
    body = graphene.String()

class PostsNew(graphene.Mutation):
    class Arguments:
        document = PostsInput()

    document = graphene.Field(PostType)
    _id = graphene.String(name="_id")
    slug = graphene.String()

    def resolve__id(self, info):
        return self.document.id

    def resolve_slug(self, info):
        return self.document.slug

    @staticmethod
    def mutate(root, info, document=None):
        user = info.context.user
        posted_at = datetime.today()
        _id = make_id(user.username,
                      posted_at.replace(tzinfo=timezone.utc).timestamp())
        slug = document.title.strip().lower().replace(" ", "-")[:60]
        post = Post(id=_id,
                    posted_at=posted_at,
                    user=user,
                    title=document.title,
                    slug=slug,
                    body=document.body,
                    draft=False)
        #TODO: Is this how I'm supposed to be saving my post or is there framework magic?
        post.save()
        return PostsNew(document=post)
            
    
class CommentsTerms(graphene.InputObjectType):
    """Search terms for the comments_total and the comments_list."""
    limit = graphene.Int()
    post_id = graphene.String()
    view = graphene.String()

class PostsTerms(graphene.InputObjectType):
    """Search terms for the posts_list."""
    limit = graphene.Int()
    post_id = graphene.String()
    view = graphene.String()
    # Legacy field for LW 2 compatibility
    meta = graphene.Boolean()
    
class Query(object):

    login = graphene.Field(graphene.String,
                          username=graphene.String(),
                          password=graphene.String(),
                          name="Login")
    users_single = graphene.Field(UserType,
                                  id=graphene.Int(),
                                  username=graphene.String(),
                                  document_id=graphene.String(),
                                  name="UsersSingle")
    all_users = graphene.List(UserType)
    posts_single = graphene.Field(PostType,
                                  _id=graphene.String(name="_id"),
                                  posted_at=graphene.types.datetime.DateTime(),
                                  frontpage_date = graphene.types.datetime.Date(),
                                  curated_date = graphene.types.datetime.Date(),
                                  userId = graphene.String(),
                                  document_id = graphene.String(),
                                  name="PostsSingle")
    all_posts = graphene.List(PostType)
    posts_list = graphene.Field(graphene.List(PostType),
                                terms = graphene.Argument(PostsTerms),
                                name="PostsList")
    posts_new = graphene.Field(PostType,
                               _id = graphene.String(name="_id"),
                               slug = graphene.String(),
                               name="PostsNew")
    comment = graphene.Field(CommentType,
                             id=graphene.String(),
                             posted_at=graphene.types.datetime.Date(),
                             userId = graphene.Int())
    all_comments = graphene.List(CommentType)

    comments_total = graphene.Field(graphene.types.Int,
                                    terms = graphene.Argument(CommentsTerms),
                                    name="CommentsTotal")

    comments_list = graphene.Field(graphene.List(CommentType),
                                   terms = graphene.Argument(CommentsTerms),
                                   name="CommentsList")
    comments_new = graphene.Field(CommentType,
                                  _id = graphene.String(name="_id"))

    comments_edit = graphene.Field(CommentType,
                                   _id = graphene.String(name="_id"))
    
    vote = graphene.Field(VoteType,
                          id=graphene.Int())

    all_votes = graphene.List(VoteType)

    def resolve_login(self, info, **kwargs):
        username = kwargs.get('username')
        password = kwargs.get('password')
        user = authenticate(info.context, username=username, password=password)
        if user is not None:
            login(info.context, user)
            return info.context.session.session_key
        else:
            return None
    
    def resolve_users_single(self, info, **kwargs):
        id = kwargs.get('id')
        document_id = kwargs.get('document_id')
        username = kwargs.get('username')

        if id:
            return User.objects.get(id=id)
        if document_id:
            # Mongodb uses this field for uid lookups, we do it for compatibility
            return User.objects.get(id=document_id)
        if username:
            return User.objects.get(username=username)

        return None
    
    def resolve_all_users(self, info, **kwargs):
        return User.objects.all()

    def resolve_posts_single(self, info, **kwargs):
        id = kwargs.get('document_id')
        if id:
            return Post.objects.get(id=id)

        return None
        
    def resolve_all_posts(self, info, **kwargs):
        #TODO: Figure out a better way to maintain compatibility here
        #...If there is one.
        return PostType.objects.all()

    def resolve_posts_list(self, info, **kwargs):
        #TODO: Make this actually return the top 20 posts
        return Post.objects.all()

    def resolve_comment(self, info, **kwargs):
        id = kwargs.get('id')

        if id:
            return Post.objects.get(id=id)

        return None

    def resolve_all_comments(self, info, **kwargs):
        return Comment.objects.select_related('post').all()

    def resolve_comments_total(self, info, **kwargs):
        args = dict(kwargs.get('terms'))
        id = args.get('post_id')
        try:
            return Post.objects.get(id=id).comment_count
        except:
            return 0

    def resolve_comments_list(self, info, **kwargs):
        args = dict(kwargs.get('terms'))
        id = args.get('post_id')
        view = args.get('view')
        if view == 'recentComments':
            return Comment.objects.all()
            
        try:
            document = Post.objects.get(id=id)
            return document.comments.all()
        except:
            return graphene.List(CommentType, resolver=lambda x,y: [])

    def resolve_vote(self, info, **kwargs):
        id = kwargs.get('id')

        if id:
            return Vote.objects.get(id=id)

        return None
        

class Mutations(object):
    posts_new = PostsNew.Field(name="PostsNew")
    comments_new = CommentsNew.Field(name="CommentsNew")
    comments_edit = CommentsEdit.Field(name="CommentsEdit")
