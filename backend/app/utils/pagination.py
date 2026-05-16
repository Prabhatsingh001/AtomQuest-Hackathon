"""Pagination utilities."""

from typing import TypeVar, Generic, List, Optional
from pydantic import BaseModel

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Query parameters model for list endpoint pagination.

    Attributes:
        page: Current requested page number (1-indexed).
        page_size: Number of items requested per page.
    """
    page: int = 1
    page_size: int = 20

    @property
    def offset(self) -> int:
        """Calculate SQL database query offset.

        Returns:
            int: The computed offset integer based on page and page_size.
        """
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel):
    """Generic envelope model for paginated API responses.

    Attributes:
        items: List of paginated items for the current slice.
        total: Total count of items matching query across all pages.
        page: Current active page index.
        page_size: Number of items requested per page.
        total_pages: Total computed pages available.
    """
    items: list
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def create(cls, items: list, total: int, page: int, page_size: int):
        """Construct a paginated response instance from raw query counts.

        Args:
            items: Current page slice of records.
            total: Aggregate count of matching database records.
            page: Current requested page number.
            page_size: Active limit per page.

        Returns:
            PaginatedResponse: An initialized paginated wrapper structure.
        """
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
