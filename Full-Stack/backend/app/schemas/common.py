from math import ceil
from typing import Generic, TypeVar

from pydantic import BaseModel, Field


T = TypeVar("T")


class PaginationQuery(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class PageMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    meta: PageMeta


def build_page_meta(page: int, page_size: int, total: int) -> PageMeta:
    return PageMeta(page=page, page_size=page_size, total=total, total_pages=max(1, ceil(total / page_size)))
