class Page:
    """A basic page class which is meant to be used across pagestores. 

    This exists to provide a uniform interface to and from pagestores 
    independent of any one pagestore's internal representation of a page. In
    theory a pagestore can use anything from database backed django models to
    custom classes which read from flat files. In order to keep things 
    consistent, this class defines the canonical format which is expected to be
    outputted and handled by pagestore implementations."""
    def __init__(self, id: int, title: str, author: str,
                 date_created: float, slug: str, body: str,
                 url: str = None, view_count: int = 0, base_score: int = 0,
                 draft: bool = True) -> type(None):
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

    
                 
