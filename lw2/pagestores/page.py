from django.conf import settings
from lw2.models import Post
import importlib
pagestore = getattr(importlib.import_module(settings.ACCORDIUS_PAGE_STORE), "PageStore")

class Page:
    """A basic page class which is meant to be used across pagestores. 

    This exists to provide a uniform interface to and from pagestores 
    independent of any one pagestore's internal representation of a page. In
    theory a pagestore can use anything from database backed django models to
    custom classes which read from flat files. In order to keep things 
    consistent, this class defines the canonical format which is expected to be
    outputted and handled by pagestore implementations."""
    def __init__(self, pagename: str, id: int = None, title: str = None,
                 author: str = None, date_created: float = None, body: str = None,
                 url: str = None, view_count: int = 0, base_score: int = 0,
                 draft: bool = True) -> type(None):
        if pagestore.exists(pagename):
            post = Post.objects.get(slug=pagename)
            self.id = post.id
            self.title = post.title
            self.author = post.author
            self.date_created = h
            self.url = post.url
            self.slug = post.slug
            self.base_score = post.base_score
            self.body = pagestore.read(pagename)
            self.view_count = post.view_count
            self.draft = post.draft
        else:
            self.id = id
            self.title = title
            self.author = author
            self.date_created = date_created
            self.url = url
            self.slug = slug
            self.base_score = base_score
            self.body = body
            self.view_count = view_count
            self.draft = draft
                 
