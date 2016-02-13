import unittest
from app import create_app, db
from app.uploads import views


class UserModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app, self.celeryapp = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_allowed_file(self):
        self.assertTrue(views.allowed_file_extension('test.csv'))
        self.assertTrue(views.allowed_file_extension('test'))
        self.assertFalse(views.allowed_file_extension('test.'))
        self.assertFalse(views.allowed_file_extension('test.txt'))
