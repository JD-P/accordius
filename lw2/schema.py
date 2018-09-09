from graphene_django import DjangoObjectType
import graphene
from django.contrib.auth.models import User
from .models import Post, Comment

class UserType(DjangoObjectType):
    class Meta:
        model = User

class PostType(DjangoObjectType):
    class Meta:
        model = Post
        
class CommentType(DjangoObjectType):
    class Meta:
        model = Comment
    
class Query(object):
    user = graphene.Field(UserType,
                          id=graphene.Int(),
                          username=graphene.String())
    all_users = graphene.List(UserType)
    post = graphene.Field(PostType,
                          id=graphene.String(),
                          posted_at=graphene.types.datetime.Date(),
                          frontpage_date = graphene.types.datetime.Date(),
                          curated_date = graphene.types.datetime.Date(),
                          userId = graphene.Int())
    all_posts = graphene.List(PostType)
    all_comments = graphene.List(CommentType)

    def resolve_user(self, info, **kwargs):
        id = kwargs.get('id')
        username = kwargs.get('username')

        if id:
            return User.objects.get(id=id)
        if username:
            return User.objects.get(username=username)

        return None
    
    def resolve_all_users(self, info, **kwargs):
        return User.objects.all()

    def resolve_post(self, info, **kwargs):
        id = kwargs.get('id')
        
        if id:
            return Post.objects.get(id=id)

        return None
        
    def resolve_all_posts(self, info, **kwargs):
        return Post.objects.all()

    def resolve_all_comments(self, info, **kwargs):
        return Comment.objects.all()
