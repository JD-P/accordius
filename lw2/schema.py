from graphene_django import DjangoObjectType
import graphene
from graphene.types.generic import GenericScalar
from django.contrib.auth.models import User
from .models import Profile, Post, Comment, Vote
import pdb

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
    user_id = graphene.Int()
    post_id = graphene.String()
    parent_comment_id = graphene.String()
    page_url = graphene.String(default_value="")
    all_votes = graphene.List(VoteType, resolver=lambda x,y: [])
    html_body = graphene.String(default_value="Test comment")
    
    def resolve__id(self, info):
        return self.id
    
    def resolve_user_id(self, info):
        return self.user.id

    def resolve_post_id(self, info):
        return self.post.id

    def resolve_parent_comment_id(self, info):
        return self.parent_comment.id

class PostType(DjangoObjectType):
    class Meta:
        model = Post
    _id = graphene.String(name="_id")
    user_id = graphene.String()
    page_url = graphene.String(default_value="")
    word_count = graphene.Int(default_value=1)
    all_votes = graphene.List(VoteType, resolver=lambda x,y: [])

    def resolve__id(self,info):
        #TODO: Make sure we actually grab the correct value here
        document_id = info.operation.selection_set.selections[0].arguments[0].value.value
        try:
            document = Post.objects.get(id=document_id)
        except:
            return "error"
        return document_id
    
    def resolve_user_id(self, info):
        #TODO: Make sure we actually grab the correct value here
        document_id = info.operation.selection_set.selections[0].arguments[0].value.value
        try:
            document = Post.objects.get(id=document_id)
        except:
            return "error"
        return document.user.id

class CommentsTerms(graphene.InputObjectType):
    """Search terms for the comments_total and the comments_list."""
    limit = graphene.Int()
    post_id = graphene.String()
    view = graphene.String()
    
class Query(object):
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

    vote = graphene.Field(VoteType,
                          id=graphene.Int())

    all_votes = graphene.List(VoteType)
    
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
        
