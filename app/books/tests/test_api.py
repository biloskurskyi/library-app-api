from rest_framework.test import APITestCase

from books.models import Book
from users.models import UserType
from users.tests.test_api import create_user


def create_book(title='Dune', author='Frank Herbert', total_copies=5, available_copies=5):
    return Book.objects.create(
        title=title,
        author=author,
        total_copies=total_copies,
        available_copies=available_copies,
    )


class BookListApiTests(APITestCase):
    def test_list_requires_authentication(self):
        res = self.client.get('/api/books/')
        self.assertEqual(res.status_code, 401)

    def test_list_empty(self):
        self.client.force_authenticate(create_user())
        res = self.client.get('/api/books/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data, [])

    def test_list_ordered_by_title(self):
        zebra = create_book(title='Zebra')
        alpha = create_book(title='Alpha')
        self.client.force_authenticate(create_user())
        res = self.client.get('/api/books/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data, [
            {'id': alpha.id, 'title': 'Alpha', 'author': 'Frank Herbert', 'total_copies': 5, 'available_copies': 5},
            {'id': zebra.id, 'title': 'Zebra', 'author': 'Frank Herbert', 'total_copies': 5, 'available_copies': 5},
        ])


class BookCreateApiTests(APITestCase):
    def setUp(self):
        self.staff = create_user(email='staff@example.com', user_type=UserType.LIBRARY, name='Staff')

    def test_create(self):
        self.client.force_authenticate(self.staff)
        res = self.client.post('/api/books/', {'title': 'Dune', 'author': 'Frank Herbert', 'total_copies': '11'})
        self.assertEqual(res.status_code, 201)
        book = Book.objects.get(pk=res.data['id'])
        self.assertEqual(res.data, {
            'id': book.id,
            'title': 'Dune',
            'author': 'Frank Herbert',
            'total_copies': 11,
            'available_copies': 11,
        })

    def test_create_ignores_available_copies(self):
        self.client.force_authenticate(self.staff)
        payload = {'title': 'Dune', 'author': 'Frank Herbert', 'total_copies': 5, 'available_copies': 1}
        res = self.client.post('/api/books/', payload)
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data['available_copies'], 5)

    def test_create_by_visitor_fails(self):
        self.client.force_authenticate(create_user())
        res = self.client.post('/api/books/', {'title': 'Dune', 'author': 'Frank Herbert', 'total_copies': 5})
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.data['code'], 'PERMISSION_DENIED')

    def test_create_duplicate_title_author_fails(self):
        create_book()
        self.client.force_authenticate(self.staff)
        res = self.client.post('/api/books/', {'title': 'Dune', 'author': 'Frank Herbert', 'total_copies': 5})
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.data['code'], 'VALIDATION_ERROR')

    def test_create_negative_total_copies_fails(self):
        self.client.force_authenticate(self.staff)
        res = self.client.post('/api/books/', {'title': 'Dune', 'author': 'Frank Herbert', 'total_copies': -1})
        self.assertEqual(res.status_code, 400)

    def test_create_missing_fields_fails(self):
        self.client.force_authenticate(self.staff)
        res = self.client.post('/api/books/', {'title': 'Dune'})
        self.assertEqual(res.status_code, 400)


class BookDetailApiTests(APITestCase):
    def test_detail(self):
        book = create_book()
        self.client.force_authenticate(create_user())
        res = self.client.get(f'/api/books/{book.pk}/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data, {
            'id': book.id,
            'title': 'Dune',
            'author': 'Frank Herbert',
            'total_copies': 5,
            'available_copies': 5,
        })

    def test_detail_missing_fails(self):
        self.client.force_authenticate(create_user())
        res = self.client.get('/api/books/999/')
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.data['code'], 'NOT_FOUND')

    def test_detail_requires_authentication(self):
        res = self.client.get('/api/books/1/')
        self.assertEqual(res.status_code, 401)


class BookUpdateApiTests(APITestCase):
    def setUp(self):
        self.staff = create_user(email='staff@example.com', user_type=UserType.LIBRARY, name='Staff')
        self.book = create_book(total_copies=5, available_copies=2)
        self.client.force_authenticate(self.staff)

    def refreshed(self):
        self.book.refresh_from_db()
        return self.book

    def test_patch_title(self):
        res = self.client.patch(f'/api/books/{self.book.pk}/', {'title': 'Dune Messiah'})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['title'], 'Dune Messiah')
        self.assertEqual(self.refreshed().title, 'Dune Messiah')

    def test_patch_total_below_available_clamps(self):
        res = self.client.patch(f'/api/books/{self.book.pk}/', {'total_copies': 1})
        self.assertEqual(res.status_code, 200)
        book = self.refreshed()
        self.assertEqual(book.total_copies, 2)
        self.assertEqual(book.available_copies, 2)

    def test_patch_total_above_total_expands_available(self):
        res = self.client.patch(f'/api/books/{self.book.pk}/', {'total_copies': 8})
        self.assertEqual(res.status_code, 200)
        book = self.refreshed()
        self.assertEqual(book.total_copies, 8)
        self.assertEqual(book.available_copies, 5)

    def test_patch_total_within_range_sets_directly(self):
        res = self.client.patch(f'/api/books/{self.book.pk}/', {'total_copies': 3})
        self.assertEqual(res.status_code, 200)
        book = self.refreshed()
        self.assertEqual(book.total_copies, 3)
        self.assertEqual(book.available_copies, 2)

    def test_patch_title_and_total_together(self):
        res = self.client.patch(f'/api/books/{self.book.pk}/', {'title': 'Dune Messiah', 'total_copies': 8})
        self.assertEqual(res.status_code, 200)
        book = self.refreshed()
        self.assertEqual(book.title, 'Dune Messiah')
        self.assertEqual(book.total_copies, 8)
        self.assertEqual(book.available_copies, 5)

    def test_patch_total_string_coerced(self):
        res = self.client.patch(f'/api/books/{self.book.pk}/', {'total_copies': '12'})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(self.refreshed().total_copies, 12)

    def test_patch_total_negative_fails(self):
        res = self.client.patch(f'/api/books/{self.book.pk}/', {'total_copies': -1})
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.data['code'], 'VALIDATION_ERROR')

    def test_patch_total_garbage_fails(self):
        res = self.client.patch(f'/api/books/{self.book.pk}/', {'total_copies': 'many'})
        self.assertEqual(res.status_code, 400)

    def test_patch_available_copies_ignored(self):
        res = self.client.patch(f'/api/books/{self.book.pk}/', {'available_copies': 99})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(self.refreshed().available_copies, 2)

    def test_patch_duplicate_title_author_fails(self):
        create_book(title='Dune Messiah')
        res = self.client.patch(f'/api/books/{self.book.pk}/', {'title': 'Dune Messiah'})
        self.assertEqual(res.status_code, 400)

    def test_patch_by_visitor_fails(self):
        self.client.force_authenticate(create_user())
        res = self.client.patch(f'/api/books/{self.book.pk}/', {'title': 'Dune Messiah'})
        self.assertEqual(res.status_code, 403)

    def test_patch_missing_book_fails(self):
        res = self.client.patch('/api/books/999/', {'title': 'Dune Messiah'})
        self.assertEqual(res.status_code, 404)

    def test_put_not_allowed(self):
        res = self.client.put(f'/api/books/{self.book.pk}/', {'title': 'Dune Messiah'})
        self.assertEqual(res.status_code, 405)
        self.assertEqual(res.data['code'], 'METHOD_NOT_ALLOWED')


class BookDeleteApiTests(APITestCase):
    def setUp(self):
        self.staff = create_user(email='staff@example.com', user_type=UserType.LIBRARY, name='Staff')
        self.client.force_authenticate(self.staff)

    def test_delete(self):
        book = create_book()
        res = self.client.delete(f'/api/books/{book.pk}/')
        self.assertEqual(res.status_code, 204)
        self.assertFalse(Book.objects.filter(pk=book.pk).exists())

    def test_delete_with_borrowed_copies_fails(self):
        book = create_book(total_copies=5, available_copies=4)
        res = self.client.delete(f'/api/books/{book.pk}/')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.data['detail'], ['Cannot delete the book because some copies are currently borrowed.'])
        self.assertTrue(Book.objects.filter(pk=book.pk).exists())

    def test_delete_by_visitor_fails(self):
        book = create_book()
        self.client.force_authenticate(create_user())
        res = self.client.delete(f'/api/books/{book.pk}/')
        self.assertEqual(res.status_code, 403)

    def test_delete_missing_fails(self):
        res = self.client.delete('/api/books/999/')
        self.assertEqual(res.status_code, 404)
