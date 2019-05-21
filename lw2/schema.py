from graphene_django import DjangoObjectType
import graphene
from graphene.types.generic import GenericScalar
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.db.models.functions import Greatest
from .models import Profile,Vote, Notification, Conversation, Participant
from .models import Message as MessageModel
from .models import Post as PostModel
from .models import Comment as CommentModel
from .markdown import md
from datetime import datetime, timezone

import hashlib
import base64

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
        
    _id = graphene.String(name="_id")
    slug = graphene.String()
    display_name = graphene.String()
    karma = graphene.Int()
    last_notifications_check = graphene.types.datetime.Date()

    def resolve__id(self, info):
        return str(self.id)
    
    def resolve_slug(self, info):
        return self.username

    def resolve_display_name(self, info):
        try:
            display_name = self.profile.display_name
        except AttributeError:
            print("User {} has no profile!".format(self.username))
            display_name = self.username
        if display_name:
            return display_name
        else:
            return self.username

    def resolve_karma(self, info):
        try:
            return self.profile.karma
        except AttributeError:
            raise ValueError("User {} has no profile!".format(self.username))

    def resolve_last_notifications_check(self, info):
        try:
            return self.profile.last_notifications_check
        except AttributeError:
            raise ValueError("User {} has no profile!".format(self.username))

class UsersInput(graphene.InputObjectType):
    last_notifications_check = graphene.types.datetime.DateTime()

class UsersEdit(graphene.Mutation):
    class Arguments:
        document_id = graphene.String()
        set = UsersInput()

    _id = graphene.String(name="_id")
        
    @staticmethod
    def mutate(root, info, document_id=None, set=None):
        user = User.objects.get(id=document_id)
        if not (user == info.context.user and info.context.user.is_authenticated):
            raise ValueError(
                "Trying to change properties of user {} but logged in as {}".format(
                    user.username,
                    info.context.user.username)
                )
        try:
            profile = Profile.objects.get(user=user)
        except Profile.DoesNotExist:
            profile = Profile(user=user)
                              
        if set.last_notifications_check:
            profile.last_notifications_check = set.last_notifications_check

        profile.save()
        return UsersEdit(_id=str(user.id))
        
               
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
        return str(self.id)
        
        
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
    retracted = graphene.Boolean(description="Whether the author has retracted their comment.")
    #TODO: Make this a placeholder that always returns false and just don't return deleted comments
    deleted_public = graphene.Boolean(
        description="Whether this comment has been deleted from view.")
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
        if self.is_deleted:
            return "<p>[This post has been deleted]</p>"
        return md.convert(self.body)

    def resolve_vote_count(self, info):
        return Vote.objects.filter(document_id=self.id).count()

    def resolve_current_user_votes(self, info):
        try:
            return Vote.objects.filter(user=info.context.user,
                                       document_id=self.id)
        except IndexError:
            return []

    def resolve_retracted(self, info):
        return self.retracted

    def resolve_deleted_public(self, info):
        return self.is_deleted
    
    def resolve_af(self, info):
        """Legacy field for whether this is the Alignment Forum, always false."""
        return False

class CommentsInput(graphene.InputObjectType):
    body = graphene.String()
    post_id = graphene.String()
    parent_comment_id = graphene.String()
    last_edited_as = graphene.String()
    
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

    def resolve_comment_count(self, info):
        """Derived field that returns the number of comments on a given post."""
        return self.comments.count()
    
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
    last_edited_as = graphene.String()
    question = graphene.Boolean()
    meta = graphene.Boolean()
    draft = graphene.Boolean()

class PostsUnset(graphene.InputObjectType):
    meta = graphene.Boolean()
    draft = graphene.Boolean()
    url = graphene.Boolean()  

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
        if not document.title:
            raise ValueError("Can't make a post with an empty title!")
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

    def resolve__id(self, info):
        return self.post.id

    def resolve_slug(self, info):
        return self.post.slug
    
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
        post.body = set.body
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
    offset = graphene.Int()
    post_id = graphene.String()
    user_id = graphene.String()
    view = graphene.String()

class PostsTerms(graphene.InputObjectType):
    """Search terms for the posts_list."""
    limit = graphene.Int()
    offset = graphene.Int()
    post_id = graphene.String()
    user_id = graphene.String()
    view = graphene.String()
    # Legacy field for LW 2 compatibility
    # Should be boolean, but sometimes presents as null so generic required 
    meta = graphene.Boolean()
    
class NotificationsTerms(graphene.InputObjectType):
    """Search terms for the notifications."""
    limit = graphene.Int()
    offset = graphene.Int()
    user_id = graphene.String()
    view = graphene.String()

class MessagesTerms(graphene.InputObjectType):
    conversation_id = graphene.String()
    view = graphene.String()
    
class NotificationType(DjangoObjectType):
    class Meta:
        model = Notification

    _id = graphene.String(name="_id")
    title = graphene.String()
    link = graphene.String()

    def resolve__id(self, info):
        return str(self.id)

    def resolve_title(self, info):
        # Just do a dummy resolver for now
        return "Test title"
    
    def resolve_link(self, info):
        # Just do a dummy resolver for now
        return None

class ParticipantType(DjangoObjectType):
    class Meta:
        model = Participant

    display_name = graphene.String()
    slug = graphene.String()

    def resolve_display_name(self, info):
        display_name = self.user.profile.get(user=self.user).display_name
        if display_name:
            return display_name
        else:
            return self.user.username
    def resolve_slug(self, info):
        return self.user.username
    
class ConversationsInput(graphene.InputObjectType):
    participant_ids = graphene.List(graphene.String)
    title = graphene.String()
    
class ConversationType(DjangoObjectType):
    class Meta:
        model = Conversation

    _id = graphene.String(name="_id")
    participants = graphene.List(ParticipantType)
    
    def resolve__id(self, info):
        return str(self.id)

    def resolve_participants(self, info):
        return self.participants.all()
    
class ConversationsNew(graphene.Mutation):
    class Arguments:
        document = ConversationsInput()

    _id = graphene.String(name="_id")
        
    @staticmethod
    def mutate(root, info, document=None):
        if not document:
            raise ValueError(
                "No conversation variables were passed, got '{}' instead.".format(
                    repr(document)
                    )
            )
        convo = Conversation(title=document.title)
        convo.save()
        #TODO: Delete convo if we get error here
        for participant_id in document.participant_ids:
            user = User.objects.get(id=int(participant_id))
            participant = Participant(user=user,
                                      conversation=convo)
            participant.save()
        return ConversationsNew(_id=convo.id)
    
class MessagesInput(graphene.InputObjectType):
    conversation_id = graphene.String()
    body = graphene.String()

class Message(DjangoObjectType):
    class Meta:
        model = MessageModel

    _id = graphene.String(name="_id")
    user_id = graphene.String()
    html_body = graphene.String()
    posted_at = graphene.types.datetime.DateTime()
    
    def resolve__id(self, info):
        return str(self.id)
    
    def resolve_user_id(self, info):
        return str(self.user.id)

    def resolve_posted_at(self, info):
        return self.created_at
    
    def resolve_html_body(self, info):
        return md.convert(self.body)

class MessagesNew(graphene.Mutation):
    class Arguments:
        document = MessagesInput()

    _id = graphene.String(name="_id")

    @staticmethod
    def mutate(root, info, document=None):
        if not document:
            raise ValueError(
                "No conversation variables were passed, got '{}' instead.".format(
                    repr(document)
                    )
            )
        if not info.context.user.is_authenticated:
            raise ValueError("You need to be logged in to send private messages")
        
        conversation = Conversation.objects.get(id=int(document.conversation_id))
        message_text = document.body
        message = MessageModel(user=info.context.user,
                               conversation=conversation,
                               body=message_text)
        message.save()
        return MessagesNew(_id=message.id)
        
    
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

    notifications_list = graphene.Field(graphene.List(NotificationType),
                                        terms = graphene.Argument(NotificationsTerms),
                                        name="NotificationsList")
    conversations_single = graphene.Field(ConversationType,
                                          document_id = graphene.String(),
                                          name="ConversationsSingle")
    messages_list = graphene.Field(graphene.List(Message),
                                   terms = graphene.Argument(MessagesTerms),
                                   name="MessagesList")
    
    def resolve_users_single(self, info, **kwargs):
        id = kwargs.get('id')
        document_id = kwargs.get('document_id')
        slug = kwargs.get('slug')

        if id:
            id = int(id)
            return User.objects.get(id=id)
        if document_id:
            document_id = int(document_id)
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
        return PostModel.objects.all().annotate(test=Greatest('posted_at','comments__posted_at')).order_by('-test')

    def resolve_posts_list(self, info, **kwargs):
        args = kwargs.get("terms")
        if args.user_id:
            user = User.objects.get(id=args.user_id)
            return PostModel.objects.filter(user=user)
        if args.limit and args.offset:
            return PostModel.objects.all().annotate(test=Greatest('posted_at','comments__posted_at')).order_by('-test')[args.offset:args.offset + args.limit]
        elif args.limit:
            return PostModel.objects.all().annotate(test=Greatest('posted_at','comments__posted_at')).order_by('-test')[:args.limit]
        return PostModel.objects.all().annotate(test=Greatest('posted_at','comments__posted_at')).order_by('-test')

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
        if "user_id" in args:
            user = User.objects.get(id=int(args["user_id"]))
            return CommentModel.objects.filter(user=user)
        elif "post_id" in args:
            try:
                document = PostModel.objects.get(id=args["post_id"])
                return document.comments.all()
            except:
                return graphene.List(Comment, resolver=lambda x,y: [])
        else:
            return CommentModel.objects.all().order_by('-posted_at')

            
    def resolve_vote(self, info, **kwargs):
        id = kwargs.get('id')

        if id:
            return Vote.objects.get(id=id)

        raise ValueError("No vote found for ID '{}'.".format(id))

    def resolve_notifications_list(self, info, **kwargs):
        args = kwargs["terms"]
        if not args.user_id:
            raise ValueError(
                "No user with ID '{}' found".format(info.context.user.id)
            )
        if args.view == "userNotifications":
            user = User.objects.get(id=args.user_id)
            #TODO: Implement offset
            if args.limit:
                return Notification.objects.filter(user=user)[:args.limit]
            else:
                return Notification.objects.filter(user=user)

    def resolve_conversations_single(self, info, **kwargs):
        document_id = kwargs["document_id"]
        if document_id:
            return Conversation.objects.get(id=int(document_id))
        else:
            raise ValueError("Expected document id, instead got '{}'".format(
                repr(document_id)
                )
            )

    def resolve_messages_list(self, info, **kwargs):
        #if not info.context.user.is_authenticated:
        #    raise ValueError("Need to be logged in to read private messages!")
        convo_id = kwargs["terms"].conversation_id
        return Conversation.objects.get(id=int(convo_id)).messages.all()
    

class Mutations(object):
    users_edit = UsersEdit.Field(name="usersEdit")
    login = Login.Field(name="Login")
    vote = NewVote.Field(name="vote")
    posts_new = PostsNew.Field(name="PostsNew")
    posts_edit = PostsEdit.Field(name="PostsEdit")
    comments_new = CommentsNew.Field(name="CommentsNew")
    comments_edit = CommentsEdit.Field(name="CommentsEdit")
    conversations_new = ConversationsNew.Field(name="ConversationsNew")
    messages_new = MessagesNew.Field(name="MessagesNew")

