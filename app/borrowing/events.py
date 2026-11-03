from dataclasses import dataclass


@dataclass(frozen=True)
class BookBorrowed:
    book_title: str
    member_name: str
    member_email: str


@dataclass(frozen=True)
class BookReturned:
    book_title: str
    member_name: str
    member_email: str
