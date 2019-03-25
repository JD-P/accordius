from lw2.pagestore import AbstractPageStore, PageDoesNotExist
from lw2.models import Post
import lw2
from .page import Page
from datetime import datetime


class SimplePageStore(AbstractPageStore):
    """A page store implementing the pre-wiki page retrieval, creation and 
    update functionality."""
    
    def read(self, pagename: str) -> Page:
        try:
            post = Post.objects.get(slug=pagename)
        except lw2.models.Post.DoesNotExist:
            raise PageDoesNotExist(
                "No such page '{}'".format(pagename)
            ) from None
        return Page(
            post.id, post.title, post.user.username,
            post.posted_at.timestamp(), post.slug,
            post.body, url=post.url, base_score=post.base_score, view_count=post.view_count,
            draft=post.draft
        )

    def write(self, pagename: str, page: Page) -> type(None):
        if self.exists(pagename):
            post = Post.objects.get(slug=pagename)
        else:
            post = Post()
        post.id = page.id
        post.title = page.title
        post.author = page.author
        post.posted_at = datetime.fromtimestamp(page.date_created)
        post.url = page.url
        post.slug = page.slug
        post.base_score = page.base_score
        post.body = page.body
        post.view_count = page.view_count
        post.draft = page.draft

        post.full_clean()
        post.save()

    def exists(self, pagename: str) -> bool:
        try:
            Post.objects.get(slug=pagename)
            return True
        except lw2.models.Post.DoesNotExist:
            return False

    def list(self, collection: str = "recent50") -> list:
        # TODO: Make this actually return stuff
        return []
