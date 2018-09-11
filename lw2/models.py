from datetime import date, datetime
from django.db import models
from django.contrib.auth.models import User


# Create your models here.

class Profile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    display_name = models.CharField(max_length=40)

class Post(models.Model):
    """A post object.

    - id: A 17 character truncated base64-encoded md5 hash.
    - posted_at: The time at which the post was made available, as opposed
    to draft creation.
    - frontpage_date: The time at which the post was put "on the front page",
    whatever that means in our software.
    - curated_date: The time at which the post was featured or put in the really
    good section, whatever that means in our software.
    - user: The author of the post as a user object.
    - title: The post's title.
    - url: A url that's submitted to create a link post, NOT the url of the post
    on the software instance's website.
    - base_score: The score of the post.
    - comment_count: The number of comments on the post.
    - view_count: How many views the post has gotten since it was published.
    - meta: Legacy field that says whether the post goes into the 'meta' section,
    of the website, whatever that means in our software.
    - af: Legacy field that says whether the post is part of the Alignment Forum,
    always false.
    - draft: Whether the post is a draft or not."""
    id = models.CharField(primary_key=True, max_length=17)
    posted_at = models.DateTimeField(default=datetime.today)
    frontpage_date = models.DateField(null=True, default=None)
    curated_date = models.DateField(null=True, default=None)
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    title = models.CharField(default="Untitled (this should never appear)",
                             max_length=250)
    url = models.URLField(null=True)
    slug = models.CharField(max_length=60)
    base_score = models.IntegerField(default=1)
    body = models.TextField()
    html_body = models.TextField()
    vote_count = models.IntegerField(default=0)
    comment_count = models.IntegerField(default=0)
    view_count = models.IntegerField(default=0)
    meta = models.BooleanField(default=False)
    af = models.BooleanField(default=False)
    draft = models.BooleanField(default=True)

class Comment(models.Model):
    """A comment on a Post. 

    - id: A 17 character truncated base64-encoded md5 hash.
    - user: A user object representing the comments author
    - post: The post object on which the comment was made.
    - parent_comment: If this comment is a reply to another, this field
    is the comment object representing it. 
    - posted_at: The time at which the comment was posted.
    - base_score: The score of the comment object.
    - body: A markdown text comment body.
    - af: Legacy field for whether this is the Alignment Forum, always false.
    - is_deleted: Whether the post has been hidden from public consumption."""
    id = models.CharField(primary_key=True, max_length=17)
    user = models.ForeignKey(User, related_name="comments",
                             null=True, on_delete=models.SET_NULL)
    post = models.ForeignKey(Post, related_name="comments",
                             null=True, on_delete=models.SET_NULL)
    parent_comment = models.ForeignKey('Comment',
                                       null=True, on_delete=models.SET_NULL)
    posted_at = models.DateField(default=date.today)
    base_score = models.IntegerField(default=1)
    body = models.TextField()
    af = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

class Vote(models.Model):
    """A vote on a post, comment, or other votable item.

    - user: The user object that made the vote.
    - voted_at: The date on which the vote was made.
    - power: The number of points the vote is worth, defaults to 1
    - vote_type: Whether the vote is an upvote or a downvote"""
    user = models.ForeignKey(User, related_name="votes", on_delete=models.CASCADE)
    document_id = models.CharField(max_length=17)
    voted_at = models.DateField(default=date.today)
    vote_type = models.CharField(default="smallUpvote", max_length=25)
    power = models.IntegerField(default=1)
    
class Test(models.Model):
    testfield = models.CharField(max_length=50)
