from lw2.pagestore import AbstractPageStore, PageDoesNotExist
from lw2.pagestores.versionedpagetext import VersionedPageText
from lw2.models import Post
import lw2
from datetime import datetime


class PageStore(AbstractPageStore):
    """A page store implementing the pre-wiki page retrieval, creation and 
    update functionality."""
    
    def read(self, pagename: str) -> str:
        try:
            post = Post.objects.get(slug=pagename)
        except lw2.models.Post.DoesNotExist:
            raise PageDoesNotExist(
                "No such page '{}'".format(pagename)
            ) from None
        return VersionedPageText(post.body)

    def write(self, pagename: str, page_body: VersionedPageText) -> type(None):
        if self.exists(pagename):
            post = Post.objects.get(slug=pagename)
        else:
            raise PageDoesNotExist(
                "No such page '{}'".format(pagename)
                ) from None
        post.body = page_body.text
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
