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
