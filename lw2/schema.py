from graphene_django import DjangoObjectType
import graphene
from graphene.types.generic import GenericScalar
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from .models import Profile,Vote
from .models import Post as PostModel
from .models import Comment as CommentModel
from datetime import datetime, timezone
import markdown
from mdx_bleach.extension import BleachExtension
import hashlib
import base64
import pdb

bleach = BleachExtension()
md = markdown.Markdown(extensions=[bleach])

def make_id(username, utc_timestamp):
    hashable = username + str(utc_timestamp)
    hash_raw = hashlib.md5(hashable.encode())
    hash_b64 = base64.b64encode(hash_raw.digest()).decode()
    return hash_b64[:17].replace("/","_").replace("+","-")

def make_id_from_user(username):
    """Wrapper around make_id that eliminates finnicky time handling code."""
    return make_id(username,
                   datetime.today().replace(tzinfo=timezone.utc).timestamp())
    
class UserType(DjangoObjectType):
    class Meta:
        model = User
        only_fields = {'id','_id', 'username','date_joined',
                       'posts','comments','slug',
                       'displayName','karma'}
        
    _id = graphene.Int(name="_id")
    slug = graphene.String()
    display_name = graphene.String()
    karma = graphene.Int()

    def resolve__id(self, info):
        return self.id
    
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

    def resolve_karma(self, info):
        try:
            return self.profile_set.all()[0].karma
        except IndexError:
            raise ValueError("User {} has no profile!".format(self.username))

class Login(graphene.Mutation):
    class Arguments:
        username = graphene.String()
        password = graphene.String()

    user_id = graphene.Int()
    session_key = graphene.String()
    expiration = graphene.Float()
    
    @staticmethod
    def mutate(root, info, username=None, password=None):
        user = authenticate(info.context, username=username, password=password)
        if user is not None:
            login(info.context, user)
            return Login(user_id=user.id,
                         session_key=info.context.session.session_key,
                         expiration=(
                             info.context.session.get_expiry_date().timestamp())
            )
                         
        else:
            raise ValueError("Incorrect username or password!")
        
class VoteType(DjangoObjectType):
    class Meta:
        model = Vote
        only_fields = {'document_id','voted_at','vote_type','power'}
    _id = graphene.Int(name="_id")

    def resolve__id(self, info):
        return self.id
        
        
class Comment(DjangoObjectType):
    class Meta:
        model = CommentModel
        description="A comment on a post or other commentable object."
    _id = graphene.String(name="_id",
                          description="17 character truncated base-64 encoded md5 hash.")
    user_id = graphene.String(description="ID value of the comments author.")
    post_id = graphene.String(
        description="ID value of the post on which the comment is made.")
    parent_comment_id = graphene.String(
        description="ID value of the comment above, if it exists.")
    page_url = graphene.String(default_value="")
    vote_count = graphene.Int()
    current_user_votes = graphene.List(VoteType)
    all_votes = graphene.List(VoteType, resolver=lambda x,y: [])
    html_body = graphene.String(
        description="Dynamic field that renders markdown body as html.")
    af = graphene.Boolean(
        description="Legacy field for whether we're on alignment forum, always false.")
    
    def resolve__id(self, info):
        return self.id
    
    def resolve_user_id(self, info):
        return str(self.user.id)

    def resolve_post_id(self, info):
        return self.post.id

    def resolve_parent_comment_id(self, info):
        try:
            return self.parent_comment.id
        except AttributeError:
            return None

    def resolve_html_body(self, info):
        return md.convert(self.body)

    def resolve_vote_count(self, info):
        return Vote.objects.filter(document_id=self.id).count()

    def resolve_current_user_votes(self, info):
        try:
            return Vote.objects.filter(user=info.context.user,
                                       document_id=self.id)
        except IndexError:
            return []
    
    def resolve_af(self, info):
        """Legacy field for whether this is the Alignment Forum, always false."""
        return False

class CommentsInput(graphene.InputObjectType):
    body = graphene.String()
    post_id = graphene.String()
    parent_comment_id = graphene.String()
    
class CommentsNew(graphene.Mutation):
    class Arguments:
        document = CommentsInput()

    comment = graphene.Field(Comment)
    _id = graphene.String(name="_id")

    def resolve__id(self, info):
        return self.comment.id
    
    @staticmethod
    def mutate(root, info, document=None):
        user = info.context.user
        if not document:
            return
        if not user.is_authenticated:
            raise ValueError("You're not logged in!")
        if document.parent_comment_id:
            parent_comment =  CommentModel.objects.get(id=document.parent_comment_id)
        else:
            parent_comment = None
            
        post = PostModel.objects.get(id=document.post_id)
        
        posted_at = datetime.today()
        
        _id = make_id(user.username,
                      posted_at.replace(tzinfo=timezone.utc).timestamp())
        
        comment = CommentModel(
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
    comment = graphene.Field(Comment)
    document_id = graphene.String()

    def resolve__id(self, info):
        return self.comment.id
    
    @staticmethod
    def mutate(root, info, document_id=None, set=None):
        if not set:
            raise ValueError(
                    "You have set no changes to be made.  You must change at least one thing to save it.")
        comment = CommentModel.objects.get(id=document_id)
        if info.context.user != comment.user:
            raise ValueError(
                            "WrongUserError: You are {}, but to edit this comment you need to be {}.".format(
                                                info.context.user.username, 
                                                comment.user.username))
        comment.body = set.body
        comment.save()
        return CommentsEdit(comment=comment)
    
class Post(DjangoObjectType):
    class Meta:
        model = PostModel
        description="""A post to the forum. Posts can be url posts pointing to \
        outside resources or original content hosted on the site, or both."""
    _id = graphene.String(name="_id")
    user_id = graphene.String(
        description="ID value of the user that authored the post.")
    html_body = graphene.String()
    page_url = graphene.String(default_value="")
    word_count = graphene.Int(default_value=1,
                              description="Number of words in post body.")
    all_votes = graphene.List(VoteType, resolver=lambda x,y: [])
    current_user_votes = graphene.List(VoteType, resolver=lambda x,y:[])

    meta = graphene.Boolean(
        description="""Legacy field for whether our post goes in 'meta' section, \
        may or may not exist in accordius.""")
    af = graphene.Boolean(
        description="Legacy field for whether we're in alignment forum, always false.")

    def resolve__id(self,info):
        return self.id
    
    def resolve_user_id(self, info):
        return str(self.user.id)

    def resolve_html_body(self, info):
        """Create an HTML text from the Markdown post body."""
        return md.convert(self.body)

    def resolve_meta(self, info):
        """Legacy field that says whether the post goes into the 'meta' section,
        of the website, whatever that means in our software."""
        return False

    def resolve_af(self, info):
        """Legacy field that says whether the post is part of the Alignment Forum,
        always false."""
        return False
    
class PostsInput(graphene.InputObjectType):
    title = graphene.String()
    body = graphene.String()
    url = graphene.String()

class PostsUnset(graphene.InputObjectType):
    meta = graphene.Boolean()
    draft = graphene.Boolean()
    url = graphene.String()   

class PostsNew(graphene.Mutation):
    class Arguments:
        document = PostsInput()

    document = graphene.Field(Post)
    _id = graphene.String(name="_id")
    slug = graphene.String()

    def resolve__id(self, info):
        return self.document.id

    def resolve_slug(self, info):
        return self.document.slug

    @staticmethod
    def mutate(root, info, document=None):
        user = info.context.user
        if not user.is_authenticated:
            raise ValueError("Your user isn't logged in")
        posted_at = datetime.today()
        _id = make_id(user.username,
                      posted_at.replace(tzinfo=timezone.utc).timestamp())
        slug = document.title.strip().lower().replace(" ", "-")[:60]
        post = PostModel(id=_id,
                         posted_at=posted_at,
                         user=user,
                         title=document.title,
                         slug=slug,
                         body=document.body,
                         draft=False)
        if document.url:
            post.url = document.url
        #TODO: Is this how I'm supposed to be saving my post or is there framework magic?
        post.save()
        return PostsNew(document=post)
            
class PostsEdit(graphene.Mutation):
    class Arguments:
        document_id = graphene.String()
        unset = PostsUnset()
        set = PostsInput()
    
    post = graphene.Field(Post)
    _id = graphene.String(name="_id")
    slug = graphene.String()
    @staticmethod
    def mutate(root, info, document_id=None, set=None, unset=None):
        if not set:
            raise ValueError(
                "Your set has no changes to be made.  " +
                "You must change at least one thing to save.")
        post = PostModel.objects.get(id=document_id)
        if info.context.user != post.user:
            raise ValueError(
                            "WrongUserError: You are {}, but to edit this post you need to be {}.".format(
                                                info.context.user.username, 
                                                post.user.username))
        comment.body = set.body
        if set.title != None:
            post.title = set.title
        if set.body != None:
            post.body = set.body
        if unset.url:
            post.url = None
        if unset.meta:
            post.meta = False
        if unset.draft:
            post.draft = False
        post.save()
        return PostsEdit(post=post)

class Voteable(graphene.Union):
    class Meta:
        types = (Post, Comment)
    
class NewVote(graphene.Mutation):
    class Arguments:
        document_id = graphene.String()
        vote_type = graphene.String()
        collection_name = graphene.String()

    Output = Voteable
        
    @staticmethod
    def mutate(root, info, document_id=None, vote_type=None,
               collection_name=None):
        if collection_name.lower() == "comments":
            if Vote.objects.filter(document_id=document_id):
                raise ValueError("User already voted on this")
            comment = CommentModel.objects.get(id=document_id)
            #TODO: Enforce valid vote types
            vote = Vote(user=info.context.user,
                        document_id=document_id,
                        voted_at=datetime.today(),
                        vote_type=vote_type)
            if "Upvote" in vote_type:
                comment.base_score += 1
            elif "Downvote" in vote_type:
                comment.base_score -= 1
            else:
                raise ValueError(
                    "'{}' does not appear to be upvote or downvote".format(
                        vote_type)
                )
            vote.save()
            comment.save()
            return comment
        elif collection_name.lower() == "posts":
            if Vote.objects.filter(document_id=document_id):
                raise ValueError("User already voted on this")
            post = PostModel.objects.get(id=document_id)
            #TODO: Enforce valid vote types
            vote = Vote(user=info.context.user,
                        document_id=document_id,
                        voted_at=datetime.today(),
                        vote_type=vote_type)
            if "Upvote" in vote_type:
                post.base_score += 1
            elif "Downvote" in vote_type:
                post.base_score -= 1
            else:
                raise ValueError(
                    "'{}' does not appear to be upvote or downvote".format(
                        vote_type)
                )
            vote.save()
            post.save()
            return post
        else:
            raise ValueError("Collection '{}' is not handled by accordius!".format(
                collection_name))
                
    
class CommentsTerms(graphene.InputObjectType):
    """Search terms for the comments_total and the comments_list."""
    limit = graphene.Int()
    post_id = graphene.String()
    view = graphene.String()

class PostsTerms(graphene.InputObjectType):
    """Search terms for the posts_list."""
    limit = graphene.Int()
    post_id = graphene.String()
    user_id = graphene.Int()
    view = graphene.String()
    # Legacy field for LW 2 compatibility
    # Should be boolean, but sometimes presents as null so generic required 
    meta = graphene.Boolean()

class APIDescriptions(object):
    """The description texts for the various entries in the API. Because these are 
    long they're being put in a separate container class for formatting sake."""
    login = """Log in as a user. This returns a session-id that can be passed in
    an authentication header to gain privileged actions.

    Example query: {Login(username:"admin" password:"mypassword")}
    """
    
class Query(object):
    users_single = graphene.Field(UserType,
                                  id=graphene.Int(name="_id"),
                                  slug=graphene.String(),
                                  document_id=graphene.String(),
                                  name="UsersSingle")
    all_users = graphene.List(UserType)
    post = graphene.Field(Post,
                          name="Post")
    posts_single = graphene.Field(Post,
                                  _id=graphene.String(name="_id"),
                                  posted_at=graphene.types.datetime.DateTime(),
                                  frontpage_date = graphene.types.datetime.Date(),
                                  curated_date = graphene.types.datetime.Date(),
                                  userId = graphene.String(),
                                  document_id = graphene.String(),
                                  name="PostsSingle")
    all_posts = graphene.List(Post)
    posts_list = graphene.Field(graphene.List(Post),
                                terms = graphene.Argument(PostsTerms),
                                name="PostsList")
    posts_new = graphene.Field(Post,
                               _id = graphene.String(name="_id"),
                               slug = graphene.String(),
                               name="PostsNew")
    posts_edit = graphene.Field(Post,
                                _id = graphene.String(name="_id"),
                                slug = graphene.String(),
                                name="PostsEdit")
    comment = graphene.Field(Comment,
                             id=graphene.String(),
                             posted_at=graphene.types.datetime.Date(),
                             userId = graphene.Int())
    all_comments = graphene.List(Comment)

    comments_total = graphene.Field(graphene.types.Int,
                                    terms = graphene.Argument(CommentsTerms),
                                    name="CommentsTotal")

    comments_list = graphene.Field(graphene.List(Comment),
                                   terms = graphene.Argument(CommentsTerms),
                                   name="CommentsList")
    comments_new = graphene.Field(Comment,
                                  _id = graphene.String(name="_id"))

    comments_edit = graphene.Field(Comment,
                                   _id = graphene.String(name="_id"))
    
    vote = graphene.Field(VoteType,
                          id=graphene.Int())

    all_votes = graphene.List(VoteType)        
    
    def resolve_users_single(self, info, **kwargs):
        id = kwargs.get('id')
        document_id = kwargs.get('document_id')
        slug = kwargs.get('slug')

        if id:
            return User.objects.get(id=id)
        if document_id:
            # Mongodb uses this field for uid lookups, we do it for compatibility
            return User.objects.get(id=document_id)
        if slug:
            return User.objects.get(username=slug)

        raise ValueError("No identifying field passed to resolver.  Please use ID, slug, etc.")
    
    def resolve_all_users(self, info, **kwargs):
        return User.objects.all()

    def resolve_posts_single(self, info, **kwargs):
        id = kwargs.get('document_id')
        if id:
            return PostModel.objects.get(id=id)

        raise ValueError("No post with ID '{}' found.".format(id))
        
    def resolve_all_posts(self, info, **kwargs):
        #TODO: Figure out a better way to maintain compatibility here
        #...If there is one.
        return PostModel.objects.all()

    def resolve_posts_list(self, info, **kwargs):
        args = kwargs.get("terms")
        if args.user_id:
            user = User.objects.get(id=args.user_id)
            return PostModel.objects.filter(user=user)
        #TODO: Make this actually return the top 20 posts
        return PostModel.objects.all()

    def resolve_comment(self, info, **kwargs):
        id = kwargs.get('id')

        if id:
            return PostModel.objects.get(id=id)

        raise ValueError("No comment with ID '{}' found.".format(id))

    def resolve_all_comments(self, info, **kwargs):
        return CommentModel.objects.select_related('post').all()

    def resolve_comments_total(self, info, **kwargs):
        args = dict(kwargs.get('terms'))
        id = args.get('post_id')
        try:
            return PostModel.objects.get(id=id).comment_count
        except:
            return 0

    def resolve_comments_list(self, info, **kwargs):
        args = dict(kwargs.get('terms'))
        id = args.get('post_id')
        view = args.get('view')
        if view == 'recentComments':
            return CommentModel.objects.all()
            
        try:
            document = PostModel.objects.get(id=id)
            return document.comments.all()
        except:
            return graphene.List(Comment, resolver=lambda x,y: [])

    def resolve_vote(self, info, **kwargs):
        id = kwargs.get('id')

        if id:
            return Vote.objects.get(id=id)

        raise ValueError("No vote found for ID '{}'.".format(id))        

class Mutations(object):
    login = Login.Field(name="Login")
    vote = NewVote.Field(name="vote")
    posts_new = PostsNew.Field(name="PostsNew")
    posts_edit = PostsEdit.Field(name="PostsEdit")
    comments_new = CommentsNew.Field(name="CommentsNew")
    comments_edit = CommentsEdit.Field(name="CommentsEdit")



