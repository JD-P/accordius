from abc import ABC, abstractmethod

class AbstractPageStore(ABC):
    """Abstract page store class in the vein of PmWiki's pagestore 
    functionality. 

    A pagestore abstracts the operations of creating and reading pages in the
    wiki system. This has several advantages, chief among them the ability to
    use different pagestore modules without rewriting large sections of software
    to cope. Instead, to create and use a new pagestore for accordius only this
    class has to be reimplemented. This abstract class defines the methods which
    a page store must implement for accordius to use it. It also provides 
    documentation on what those methods should take as input and return as 
    output."""

    @abstractmethod
    def read(self, pagename: str):
        pass
    
    @abstractmethod
    def write(self, pagename: str, page: dict):
        pass

    @abstractmethod
    def exists(self, pagename: str):
        pass

    @abstractmethod
    def list(self, collection: str = "recent50"):
        pass

class PageDoesNotExist(Exception):
    pass


    
