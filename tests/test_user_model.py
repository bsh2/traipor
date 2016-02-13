import unittest
import time
from app import create_app, db
from app.models import User, PendingJob, JobType


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

    def test_password_setter(self):
        u = User(password='cat')
        self.assertTrue(u.password_hash is not None)

    def test_no_password_getter(self):
        u = User(password='cat')
        with self.assertRaises(AttributeError):
            u.password

    def test_password_verification(self):
        u = User(password='cat')
        self.assertTrue(u.verify_password('cat'))
        self.assertFalse(u.verify_password('dog'))

    def test_password_salts_are_random(self):
        u = User(password='cat')
        u2 = User(password='cat')
        self.assertTrue(u.password_hash != u2.password_hash)

    def test_valid_confirmation_token(self):
        u = User(password='cat', accept_legalese=True)
        db.session.add(u)
        db.session.commit()
        token = u.generate_confirmation_token()
        self.assertTrue(u.confirm(token))

    def test_invalid_confirmation_token(self):
        u1 = User(password='cat', accept_legalese=True)
        u2 = User(password='dog', accept_legalese=True)
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        token = u1.generate_confirmation_token()
        self.assertFalse(u2.confirm(token))

    def test_expired_confirmation_token(self):
        u = User(password='cat', accept_legalese=True)
        db.session.add(u)
        db.session.commit()
        token = u.generate_confirmation_token(1)
        time.sleep(2)
        self.assertFalse(u.confirm(token))

    def test_valid_reset_token(self):
        u = User(password='cat', accept_legalese=True)
        db.session.add(u)
        db.session.commit()
        token = u.generate_reset_token()
        self.assertTrue(u.reset_password(token, 'dog'))
        self.assertTrue(u.verify_password('dog'))

    def test_invalid_reset_token(self):
        u1 = User(password='cat', accept_legalese=True)
        u2 = User(password='dog', accept_legalese=True)
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        token = u1.generate_reset_token()
        self.assertFalse(u2.reset_password(token, 'horse'))
        self.assertTrue(u2.verify_password('dog'))

    def test_has_pending_jobs(self):
        user = User(username='john', password='cat', accept_legalese=True)
        db.session.add(user)
        db.session.commit()
        user = User.query.filter_by(username='john').first()
        self.assertFalse(user.has_pending_jobs())

        job = PendingJob(owner_id=user.id, job_type=JobType.ff_fitting)
        db.session.add(job)
        db.session.commit()
        self.assertTrue(user.has_pending_jobs())
        self.assertTrue(user.has_pending_jobs(job.job_type))
        self.assertFalse(user.has_pending_jobs(JobType.ff_genplan))

        db.session.delete(job)
        db.session.commit()
        self.assertFalse(user.has_pending_jobs())
        self.assertFalse(user.has_pending_jobs(JobType.ff_fitting))
        self.assertFalse(user.has_pending_jobs(JobType.ff_genplan))
