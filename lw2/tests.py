from django.test import TestCase
from django.test import Client
from django.contrib.auth.models import User
from lw2.models import *
from datetime import datetime, timedelta
import json
import pdb

# Create your tests here.

c = Client()

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
        #TODO: Fix Markdown errors so I can log in with GraphQL
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
        
