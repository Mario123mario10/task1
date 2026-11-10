from project import db, app
import re
from datetime import date
from sqlalchemy.orm import validates

# Allowed characters for book name and author: letters (including non-ASCII, e.g. Polish),
# digits, space and a few punctuation marks. Characters such as < > " / = are not allowed,
# so HTML tags or JavaScript code cannot be stored (protection against stored XSS).
TEXT_PATTERN = re.compile(r"^[\w .,:'()!?&-]+$")
# Same limit as the length of the database columns
TEXT_MAX_LENGTH = 64

# Book model
class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, index=True)
    author = db.Column(db.String(64))
    year_published = db.Column(db.Integer)
    book_type = db.Column(db.String(20))
    status = db.Column(db.String(20), default='available')

    def __init__(self, name, author, year_published, book_type, status='available'):
        self.name = name
        self.author = author
        self.year_published = year_published
        self.book_type = book_type
        self.status = status

    # Validation of text fields displayed on the books page.
    # @validates runs on every assignment of the attribute - both in __init__ (creating a book)
    # and when editing an existing book (book.name = ...), so invalid data cannot be saved either way.
    @validates('name', 'author')
    def validate_text(self, key, value):
        """Validate and normalize the book name or author.

        Raises ValueError if the value is not a string, has an invalid length
        or contains characters outside of the allowed set.
        Returns the value with surrounding whitespace removed.
        """
        if not isinstance(value, str):
            raise ValueError(f'{key}: value must be a string')
        value = value.strip()
        # Check the length first (cheap), then the regular expression
        if not 1 <= len(value) <= TEXT_MAX_LENGTH:
            raise ValueError(f'{key}: length must be between 1 and {TEXT_MAX_LENGTH} characters')
        if not TEXT_PATTERN.match(value):
            raise ValueError(f'{key}: contains forbidden characters')
        return value

    def __repr__(self):
        return f"Book(ID: {self.id}, Name: {self.name}, Author: {self.author}, Year Published: {self.year_published}, Type: {self.book_type}, Status: {self.status})"


with app.app_context():
    db.create_all()