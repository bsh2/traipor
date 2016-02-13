import unittest
from app import create_app, db
from app.training import views
from app.training.forms import GeneratePlanForm
from app.training.plan_util import WeekDays


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

    def test_default_selection_index(self):
        defaults = ['ten', 'eleven' 'twenty']
        choices = ['ten', 'eleven' 'twenty', 'thirty', 'fourty']
        self.assertTrue(views.default_selection_index(defaults, choices) == 0)

        defaults = ['eleven', 'ten', 'twenty']
        choices = ['ten', 'eleven', 'twenty', 'thirty', 'fourty']
        self.assertTrue(views.default_selection_index(defaults, choices) == 1)

        defaults = ['foo']
        choices = ['ten', 'eleven', 'twenty', 'thirty', 'fourty']
        self.assertTrue(views.default_selection_index(defaults, choices) == 0)

        defaults = []
        choices = ['ten', 'eleven', 'twenty', 'thirty', 'fourty']
        self.assertTrue(views.default_selection_index(defaults, choices) == 0)

        defaults = ['foo']
        choices = []
        self.assertTrue(views.default_selection_index(defaults, choices) == 0)

        defaults = []
        choices = []
        self.assertTrue(views.default_selection_index(defaults, choices) == 0)

    def test_dec_list_elems(self):
        elems = [1, 2, 3]
        self.assertTrue(views.dec_list_elems(elems) == [0, 1, 2])

    def test_parse_cycle_days(self):
        form = GeneratePlanForm()
        form.mondays.data = True
        form.tuesdays.data = True
        form.wednesdays.data = True
        form.thursdays.data = False
        form.fridays.data = True
        form.saturdays.data = True
        form.sundays.data = False
        expected_res = [WeekDays.monday, WeekDays.tuesday, WeekDays.wednesday,
                        WeekDays.friday, WeekDays.saturday]
        self.assertTrue(views.parse_cycle_days(form) == expected_res)

