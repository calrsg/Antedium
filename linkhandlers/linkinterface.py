from abc import ABC, abstractmethod
from typing import List, Optional

class LinkInterface(ABC):
    """Abstract base class for link handlers."""
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the link handler.
        
        Returns
        -------
        str
            The name of the link handler.
        """
        pass

    @property
    @abstractmethod
    def link(self) -> str:
        """Return the processed link format.
        
        Returns
        -------
        str
            The link format that this handler returns.
        """        
        pass

    @property
    def status(self) -> str:
        """Return additional status message to append to fixed link.
        Default is None, but handlers may override this.
        
        Returns
        -------
        str
            The status of the link handler.
        """
        return None

    @property
    @abstractmethod
    def ignore(self) -> List[str]:
        """Return links to ignore.
        
        Returns
        -------
        List[str]
            A list of fixed link formats to ignore.
        """        
        pass

    @property
    @abstractmethod
    def replace(self) -> List[str]:
        """Return links to replace.
        
        Returns
        -------
        List[str]
            A list of link formats to replace.
        """        
        pass

    @property
    @abstractmethod
    def pattern(self) -> str:
        """Return the regex pattern for the link.
        
        Returns
        -------
        str
            A regex pattern that matches the link format.
        """
        pass

    async def resolve(self, url: str) -> Optional[str]:
        """Expand a matched URL before it is rewritten.

        Handlers for platforms that hand out short links may override this to
        look the real URL up, which requires a network request. The default is
        to hand back the URL untouched.

        Parameters
        ----------
        url : str
            The URL matched by the handler's pattern.

        Returns
        -------
        str or None
            The URL to rewrite, or None if the link could not be resolved and
            should be skipped.
        """
        return url
