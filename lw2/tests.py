from django.test import TestCase
from django.test import Client
from django.contrib.auth.models import User
from lw2.models import *
from datetime import datetime, timedelta
import json
import pdb

# Create your tests here.

c = Client()

class PostTestCase(TestCase):
    # TODO: Stop anonymous users from making posts and add unit tests for it
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'jd@jdpressman.com', 'testpassword')

    def login(self):
        response0 = c.post("/graphql/", {"query":"""
        mutation Login($user: String, $password: String) {
        Login(username: $user, password: $password) {
        userId
        sessionKey
        expiration
        }
        } """,
                                         "variables":"""{
                                         "user":"testuser",
                                         "password":"testpassword"
                                         }"""})

    def test_post_creation_plain(self):
        self.login()
        c.post("/api/posts/",
               {"title":"My Fruit Post",
                "body":"My Apple Orange Mango"})
        posts_json = c.get("/api/posts/")
        posts = json.loads(posts_json.content.decode("UTF-8"))
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0]["title"], "My Fruit Post")
        self.assertEqual(posts[0]["body"], "My Apple Orange Mango")

    def test_post_creation_url(self):
        self.login()
        c.post("/api/posts/",
               {"title":"My Fruit Post",
                "url":"https://en.wikipedia.org/wiki/Fruit",
                "body":"My Apple Orange Mango"})
        posts_json = c.get("/api/posts/")
        posts = json.loads(posts_json.content.decode("UTF-8"))
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0]["title"], "My Fruit Post")
        self.assertEqual(posts[0]["url"], "https://en.wikipedia.org/wiki/Fruit")
        self.assertEqual(posts[0]["body"], "My Apple Orange Mango")

    def test_post_creation_no_title_fails(self):
        """Test that the server will not accept a post with no title in REST 
        API.

        TODO: Write this test and make it pass."""
        response0 = c.post("/api/posts/",
                           {"title":"",
                            "url":"https://en.wikipedia.org/wiki/Fruit",
                            "body":"My Apple Orange Mango"})
        self.assertEqual(400, response0.status_code)
    
    def test_tagset_update_get(self):
        self.login()
        post = Post.objects.create(id='aaaaaaaaaaaaaaaaa', user=self.user,
                                   title='My Fruit Post',
                                   url=None, slug="test-slug-1",
                                   base_score=5,
                                   body="My Apple Orange Mango")
        response1 = c.post("/api/tags/",
                           {"document_id":post.id,
                            "text":"my"})
        response2 = c.post("/api/tags/",
                           {"document_id":post.id,
                            "text":"tag"})
        response3 = c.post("/api/tags/",
                           {"document_id":post.id,
                            "text":"set"})
        response4 = c.get("/api/posts/{}/update_tagset/".format(post.id))
        self.assertEqual(json.loads(response4.content.decode("UTF-8")).split(","),
                         ["my","tag","set"])
        
    def test_tagset_update_post(self):
        self.login()
        response0= c.post("/api/posts/",
                          {"title":"My Fruit Post",
                           "url":"https://en.wikipedia.org/wiki/Fruit",
                           "body":"My Apple Orange Mango"})
        post = json.loads(response0.content.decode("UTF-8"))
        c.post("/api/posts/" + post["_id"] + "/update_tagset/",
               {"tags":"my,tag,set"})
        response1 = c.get("/api/tags/")
        tags = json.loads(response1.content.decode("UTF-8"))
        self.assertEquals(len(tags), 3)
        self.assertEquals(set(["my","tag","set"]), set([tag["text"] for tag in tags]))

class CommentTestCase(TestCase):
    def setUp(self):
        pass

    def test_deleted_comment_no_reply(self):
        """Test that the server will not allow you to create new comments with
        a deleted comment as the parent.

        TODO: Write this test and make it pass."""
        pass

    def test_deleted_comment_replies_edit(self):
        """Test that the server will still allow you to edit existing replies 
        which have a deleted comment as the parent.

        TODO: Write this test and make it pass."""
        pass
    
    def test_deleted_comment_not_counted(self):
        """Test that deleted comments aren't counted in the numeric summary
        of how many comments are on a thread (if applicable in REST API).

        TODO: Write this test and make it pass."""
        pass
    
    def test_deleted_comment_no_vote(self):
        """Test that deleted comments cannot be voted upon.

        TODO: Write this test and make it pass."""
        pass
        
class SearchTestCase(TestCase):
    def setUp(self):
        user = User.objects.create_user('testuser', 'jd@jdpressman.com', 'testpassword')
        post1 = Post.objects.create(id='aaaaaaaaaaaaaaaaa', user=user,
                                    title='My Fruit Post',
                                    url=None, slug="test-slug-1",
                                    base_score=5,
                                    body="My Apple Orange Mango")
        post2 = Post.objects.create(id='bbbbbbbbbbbbbbbbb', user=user,
                                    title='My Animal Post',
                                    url=None, slug="test-slug-2",
                                    base_score=12,
                                    body="My Dog Cat Panda")
        post1.save()
        post2.save()

    def test_post_search_basic(self):
        search = c.get("/api/post_search/?query=Apple")
        search_data = json.loads(search.content.decode("UTF-8"))
        self.assertEquals(len(search_data), 1)
        self.assertEquals(search_data[0]["title"], "My Fruit Post")
        
    def test_post_search_and(self):
        search = c.get('/api/post_search/?query=My+Panda')
        search_data = json.loads(search.content.decode("UTF-8"))
        self.assertEquals(len(search_data), 1)
        self.assertEquals(search_data[0]["title"], "My Animal Post")

    def test_post_search_or(self):
        search = c.get('/api/post_search/?query=Apple+OR+Panda')
        search_data = json.loads(search.content.decode("UTF-8"))
        self.assertEquals(len(search_data), 2)
        self.assertTrue("My Animal Post" in [post["title"] for post in search_data])
        self.assertTrue("My Fruit Post" in [post["title"] for post in search_data])

    def test_post_search_not(self):
        search = c.get('/api/post_search/?query=-Apple')
        search_data = json.loads(search.content.decode("UTF-8"))
        self.assertEquals(len(search_data), 1)
        self.assertEquals(search_data[0]["title"], "My Animal Post")

class InviteTestCase(TestCase):
    """Test the user invite and signup API's."""
    def setUp(self):
        user = User.objects.create_user('testuser', 'jd@jdpressman.com', 'testpassword')
        user_profile = Profile()
        user_profile.user = user
        user_profile.save()

    def test_invite_creation(self):
        """Test whether the invite creation API is functioning."""
        #TODO: Log in with GraphQL
        response0 = c.post("/graphql/", {"query":"""
        mutation Login($user: String, $password: String) {
        Login(username: $user, password: $password) {
        userId
        sessionKey
        expiration
        }
        } """,
                                         "variables":"""{
                                         "user":"testuser",
                                         "password":"testpassword"
                                         }"""})
        response1 = c.post("/api/invites/", {"expires":
                                 (
                                     datetime.now() +
                                     timedelta(0, (60 * 60 * 24 * 3))
                                 ).isoformat()}
        )
        response2 = c.get("/api/my_invites/")
        invite_data = json.loads(response2.content.decode("UTF-8"))
        self.assertEquals(len(invite_data), 1)
        self.assertTrue('used_by' in invite_data[0].keys())

class TagTestCase(TestCase):
    def setUp(self):
        user = User.objects.create_user('testuser', 'jd@jdpressman.com', 'testpassword')
        user_profile = Profile()
        user_profile.user = user
        user_profile.save()

        self.post1 = Post.objects.create(id='aaaaaaaaaaaaaaaaa', user=user,
                                         title='My Fruit Post',
                                         url=None, slug="test-slug-1",
                                         base_score=5,
                                         body="My Apple Orange Mango")

    def login(self):
        response0 = c.post("/graphql/", {"query":"""
        mutation Login($user: String, $password: String) {
        Login(username: $user, password: $password) {
        userId
        sessionKey
        expiration
        }
        } """,
                                         "variables":"""{
                                         "user":"testuser",
                                         "password":"testpassword"
                                         }"""})
        
    def test_tag_creation(self):
        """Test that we can create a tag and read its contents"""
        self.login()
        response1 = c.post("/api/tags/",
                           {"document_id":self.post1.id,
                            "text":"testtag"})
        tag_id = json.loads(response1.content.decode("UTF-8"))["id"]
        response2 = c.get("/api/tags/" + str(tag_id) + "/") 
        tag_data = json.loads(response2.content.decode("UTF-8"))
        self.assertEquals(tag_data["text"], "testtag")

    def test_tag_restrictions(self):
        """Test that tags don't allow semicolons or commas at creation."""
        self.login()
        # TODO: Figure out how to display useful error message on failure
        response1 = c.post("/api/tags/",
                           {"document_id":self.post1.id,
                            "text":"my,bad,tag"})
        self.assertEquals(response1.status_code, 400)
        response2 = c.post("/api/tags/",
                           {"document_id":self.post1.id,
                            "text":"my;bad;tag"})
        self.assertEquals(response2.status_code, 400)

    def test_no_post_without_tags(self):
        """Test that it's not possible to create a post without at least one 
        tag.

        TODO: Write this test and make it pass once API is switched over."""
        pass
        
    def test_tag_delimiter_double_end(self):
        """Test that tag update strings which end with two delimiters on either
        side are still accepted by the server.

        TODO: Write this test and make it pass."""
        pass
        
    def test_tag_delimiter_mixed(self):
        """Test that strings which use both semicolons and commas as tag 
        delimiters are accepted by the API.

        TODO: Write this test and make it pass."""
        pass

    def test_whitespace_tag_fails(self):
        """Test that tags made entirely of whitespace are not accepted by the
        server.

        TODO: Write this test and make it pass."""
        pass
    
    def test_tag_duplicate_fails(self):
        """Test that you can't add the same tag twice to the same post.

        TODO: Enforce this test once I figure out what behavior I want server
        to have on this case."""
        pass

#TODO: Add unit tests for changing votes
class VoteTestCase(TestCase):
    def setUp(self):
        user = User.objects.create_user('testuser', 'jd@jdpressman.com', 'testpassword')
        user_profile = Profile()
        user_profile.user = user
        user_profile.save()

        self.post1 = Post.objects.create(id='aaaaaaaaaaaaaaaaa', user=user,
                                         title='My Fruit Post',
                                         url=None, slug="test-slug-1",
                                         base_score=5,
                                         body="My Apple Orange Mango")
        self.post1.save()

    def login(self):
        response0 = c.post("/graphql/", {"query":"""
        mutation Login($user: String, $password: String) {
        Login(username: $user, password: $password) {
        userId
        sessionKey
        expiration
        }
        } """,
                                         "variables":"""{
                                         "user":"testuser",
                                         "password":"testpassword"
                                         }"""})

    def test_vote_creation_upvote(self):
        self.login()
        response0 = c.post("/api/votes/",
                           {"document_id":self.post1.id,
                            "vote_type":"Upvote",
                            "collection_name":"posts"})
        response1 = c.get("/api/votes/")
        votes = json.loads(response1.content.decode("UTF-8"))
        self.assertEqual(votes[0]["document_id"], self.post1.id)
        self.assertEqual(votes[0]["vote_type"].lower(), "upvote")

    def test_vote_creation_downvote(self):
        self.login()
        response0 = c.post("/api/votes/",
                           {"document_id":self.post1.id,
                            "vote_type":"Downvote",
                            "collection_name":"posts"})
        response1 = c.get("/api/votes/")
        votes = json.loads(response1.content.decode("UTF-8"))
        self.assertEqual(votes[0]["document_id"], self.post1.id)
        self.assertEqual(votes[0]["vote_type"].lower(), "downvote")

    def test_vote_creation_changes_score_upvote(self):
        self.login()
        response0 = c.post("/api/votes/",
                           {"document_id":self.post1.id,
                            "vote_type":"Upvote",
                            "collection_name":"posts"})
        response1 = c.get("/api/votes/")
        post1_updated = Post.objects.all()[0]
        self.assertEqual(post1_updated.base_score,6)

    def test_vote_creation_changes_score_downvote(self):
        self.login()
        response0 = c.post("/api/votes/",
                           {"document_id":self.post1.id,
                            "vote_type":"Downvote",
                            "collection_name":"posts"})
        response1 = c.get("/api/votes/")
        post1_updated = Post.objects.all()[0]
        self.assertEqual(post1_updated.base_score,4)
