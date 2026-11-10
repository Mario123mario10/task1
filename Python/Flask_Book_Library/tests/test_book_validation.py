"""Unit tests for the validation of the Book model (protection against stored XSS)."""

import unittest
from project import app
from project.books.models import Book


def make_book(**overrides):
    """Create a Book with valid default data, replacing the fields given in overrides."""
    data = {'name': 'Pan Tadeusz', 'author': 'Adam Mickiewicz', 'year_published': 1834, 'book_type': '2days'}
    data.update(overrides)
    return Book(**data)


class TestBookValidationCorrect(unittest.TestCase):
    """Valid data - the Book object should be created."""

    def test_valid_book(self):
        book = make_book()
        self.assertEqual(book.name, 'Pan Tadeusz')
        self.assertEqual(book.author, 'Adam Mickiewicz')
        self.assertEqual(book.year_published, 1834)
        self.assertEqual(book.book_type, '2days')

    def test_polish_letters_and_punctuation(self):
        # Non-ASCII letters and allowed punctuation are accepted
        book = make_book(name="Lalka (tom 1): wydanie II", author="Bolesław Prus-Głowacki")
        self.assertEqual(book.author, 'Bolesław Prus-Głowacki')

    def test_whitespace_is_stripped(self):
        # Leading and trailing whitespace is removed before saving
        self.assertEqual(make_book(name='  Quo vadis  ').name, 'Quo vadis')

    def test_max_length(self):
        # 64 characters is the maximum allowed length
        self.assertEqual(len(make_book(name='a' * 64).name), 64)


class TestBookValidationIncorrect(unittest.TestCase):
    """Invalid data - creating the Book object should raise ValueError."""

    # Typical XSS payloads that must be rejected
    XSS_PAYLOADS = [
        "<script>alert('XSS')</script>",
        '<img src=x onerror="alert(1)">',
        '"><svg onload=alert(1)>',
        '<a href=x>link</a>',
    ]

    def test_xss_in_name(self):
        for payload in self.XSS_PAYLOADS:
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    make_book(name=payload)

    def test_xss_in_author(self):
        for payload in self.XSS_PAYLOADS:
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    make_book(author=payload)

    def test_empty_and_too_long_text(self):
        # Empty, whitespace-only and too long values are rejected
        for value in ['', '   ', 'a' * 65]:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    make_book(name=value)
                with self.assertRaises(ValueError):
                    make_book(author=value)

    def test_text_not_a_string(self):
        # Non-string values are rejected
        with self.assertRaises(ValueError):
            make_book(name=None)
        with self.assertRaises(ValueError):
            make_book(author=123)

    def test_edit_with_xss_is_rejected(self):
        # Validation also works when editing an existing book, and the old value is kept
        book = make_book()
        with self.assertRaises(ValueError):
            book.author = "<script>alert('XSS')</script>"
        self.assertEqual(book.author, 'Adam Mickiewicz')


class TestCreateBookEndpoint(unittest.TestCase):
    """The /books/create endpoint returns 400 for invalid data."""

    def setUp(self):
        self.client = app.test_client()

    def test_xss_payload_rejected(self):
        # Book with XSS payload in the author field is not created
        response = self.client.post('/books/create', json={
            'name': 'Test XSS',
            'author': "<script>alert('XSS')</script>",
            'year_published': 2000,
            'book_type': '2days',
        })
        self.assertEqual(response.status_code, 400)


if __name__ == '__main__':
    unittest.main()
