import unittest
from math import sqrt
from datetime import date
from app.training import plan_util as p_util
from app.training.plan_util import WeekDays


class PlanUtilTestCase(unittest.TestCase):

    def test_microcycle_days(self):
        days = [WeekDays.monday, WeekDays.tuesday, WeekDays.wednesday,
                WeekDays.thursday, WeekDays.friday, WeekDays.saturday,
                WeekDays.sunday]
        training_days = p_util.microcycle_days(days, 3)
        self.assertTrue(training_days == list(range(3 * 7)))
        training_days = p_util.microcycle_days([], 3)
        self.assertTrue(training_days == [])

        days = [WeekDays.monday, WeekDays.tuesday, WeekDays.wednesday,
                WeekDays.sunday]
        training_days = p_util.microcycle_days(days, 2)
        self.assertTrue(training_days == [0, 1, 2, 6, 7, 8, 9, 13])

    def test_filter_days(self):
        off_days = [6, 13, 20]
        training_days = p_util.filter_days(list(range(21)), off_days)
        for o in off_days:
            self.assertNotIn(o, training_days)

    def test_filter_weeks(self):
        off_weeks = [1, 3]
        training_days = p_util.filter_weeks(list(range(4 * 7)), off_weeks)
        self.assertTrue(training_days == list(range(7)) + list(range(14, 21)))

    def test_calc_offdays(self):
        training_days = list(range(4 * 7))
        off_days = p_util.calc_offdays(training_days, 4)
        self.assertTrue(off_days == set([]))
        training_days = list(range(3 * 7))
        off_days = p_util.calc_offdays(training_days, 4)
        self.assertTrue(off_days == set(range(3 * 7, 4 * 7)))

    def test_sort_microcycles_desc(self):
        plan = [0.1, 0.3, 0.2, 0.0, 0.5, 0.4, 0.0]
        sorted_plan = p_util.sort_microcycles(plan, True)
        self.assertTrue(sorted_plan == [0.3, 0.2, 0.1, 0.0, 0.5, 0.4, 0.0])

        plan = [0.0, 0.2, 0.3, 0.4, 0.0, 0.4, 0.6]
        sorted_plan = p_util.sort_microcycles(plan, True)
        self.assertTrue(sorted_plan == [0.0, 0.4, 0.3, 0.2, 0.0, 0.6, 0.4])

        plan = [0.1, 0.1, 0.1, 0.0, 0.1, 0.1, 0.1]
        sorted_plan = p_util.sort_microcycles(plan, True)
        self.assertTrue(sorted_plan == plan)

        plan = []
        sorted_plan = p_util.sort_microcycles(plan, True)
        self.assertTrue(sorted_plan == plan)

    def test_sort_microcycles_asc(self):
        plan = [0.1, 0.3, 0.2, 0.0, 0.5, 0.4, 0.0]
        sorted_plan = p_util.sort_microcycles(plan)
        self.assertTrue(sorted_plan == [0.1, 0.2, 0.3, 0.0, 0.4, 0.5, 0.0])

        plan = [0.0, 0.2, 0.3, 0.4, 0.0, 0.4, 0.6]
        sorted_plan = p_util.sort_microcycles(plan)
        self.assertTrue(sorted_plan == [0.0, 0.2, 0.3, 0.4, 0.0, 0.4, 0.6])

        plan = [0.1, 0.1, 0.1, 0.0, 0.1, 0.1, 0.1]
        sorted_plan = p_util.sort_microcycles(plan)
        self.assertTrue(sorted_plan == plan)

        plan = []
        sorted_plan = p_util.sort_microcycles(plan)
        self.assertTrue(sorted_plan == plan)

    def test_sort_loads(self):
        plan = [0.1, 0.3, 0.2, 0.0, 0.5, 0.4, 0.0]
        sorted_plan = p_util.sort_loads(plan)
        self.assertTrue(sorted_plan == [0.1, 0.2, 0.3, 0.0, 0.4, 0.5, 0.0])

    def test_swap_weeks(self):
        plan = [1, 2, 3, 4, 5, 6, 7, 11, 12, 13, 14, 15, 16, 17]
        swapped_plan = [11, 12, 13, 14, 15, 16, 17, 1, 2, 3, 4, 5, 6, 7]
        self.assertTrue(p_util.swap_weeks(plan, 0, 1) == swapped_plan)

    def test_sort_microcycles_asc_with_tamper_week(self):
        plan = [0.1, 0.3, 0.2, 0.0, 0.5, 0.4, 0.0,
                0.1, 0.3, 0.2, 0.0, 0.5, 0.4, 0.0,
                0.1, 0.3, 0.2, 0.0, 0.5, 0.4, 0.0]
        orderd_tampered_plan = [0.1, 0.1, 0.1, 0.0, 0.2, 0.2, 0.0,
                                0.4, 0.4, 0.5, 0.0, 0.5, 0.5, 0.0,
                                0.2, 0.3, 0.3, 0.0, 0.3, 0.4, 0.0]
        self.assertTrue(p_util.sort_microcycles_asc_with_tamper_week(plan) ==
                        orderd_tampered_plan)

    def test_sort_microcycles_dsc_with_tamper_week(self):
        plan = [0.1, 0.3, 0.2, 0.0, 0.5, 0.4, 0.0,
                0.1, 0.3, 0.2, 0.0, 0.5, 0.4, 0.0,
                0.1, 0.3, 0.2, 0.0, 0.5, 0.4, 0.0]
        orderd_tampered_plan = [0.1, 0.1, 0.1, 0.0, 0.2, 0.2, 0.0,
                                0.5, 0.4, 0.4, 0.0, 0.5, 0.5, 0.0,
                                0.3, 0.3, 0.2, 0.0, 0.4, 0.3, 0.0]
        self.assertTrue(p_util.sort_microcycles_dsc_with_tamper_week(plan) ==
                        orderd_tampered_plan)

    def test_acc_small_loads1(self):
        plan = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                0.1, 0.3, 0.2, 0.0, 0.5, 0.4, 0.0,
                0.1, 0.3, 0.2, 0.0, 0.5, 0.4, 0.0,
                0.1, 0.3, 0.2, 0.0, 0.5, 0.4, 0.0,
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6]
        plan_b = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                  0.0, 0.6, 0.0, 0.0, 0.5, 0.4, 0.0,
                  0.0, 0.6, 0.0, 0.0, 0.5, 0.4, 0.0,
                  0.0, 0.6, 0.0, 0.0, 0.5, 0.4, 0.0,
                  0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                  0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6]
        plan_c = p_util.acc_small_loads(plan, 0.45)
        plan_c = list(map(lambda x: round(x, 1), plan_c))
        self.assertTrue(plan_b == plan_c)

    def test_acc_small_loads2(self):
        plan = [0.0, 0.3, 0.2, 0.1, 0.5, 0.4, 0.0,
                0.0, 0.3, 0.2, 0.1, 0.5, 0.4, 0.0,
                0.0, 0.3, 0.2, 0.1, 0.5, 0.4, 0.0]
        plan_b = [0.0, 1.5, 0.0, 0.0, 0.0, 0.0, 0.0,
                  0.0, 1.5, 0.0, 0.0, 0.0, 0.0, 0.0,
                  0.0, 1.5, 0.0, 0.0, 0.0, 0.0, 0.0]
        plan_c = p_util.acc_small_loads(plan, 1.1)
        plan_c = list(map(lambda x: round(x, 1), plan_c))
        self.assertTrue(plan_b == plan_c)

    def test_acc_small_loads3(self):
        plan = [0.0, 0.1, 0.1, 0.1, 1.0, 1.0, 0.0,
                0.0, 0.3, 0.2, 0.1, 0.5, 0.4, 0.0]
        plan_b = [0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0,
                  0.0, 0.3, 0.3, 0.0, 0.5, 0.4, 0.0]
        plan_c = p_util.acc_small_loads(plan, 0.2, 1.0)
        plan_c = list(map(lambda x: round(x, 1), plan_c))
        self.assertTrue(plan_b == plan_c)

    def test_approximation_quality(self):
        self.assertTrue(p_util.approximation_quality(200, 100) == 50)
        self.assertTrue(p_util.approximation_quality(200, 150) == 75)
        self.assertTrue(p_util.approximation_quality(100, 200) == 50)
        self.assertTrue(p_util.approximation_quality(150, 200) == 75)

    def test_parse_comma_separated_ints(self):
        s = '1,2,3,4'
        expected = [1, 2, 3, 4]
        self.assertTrue(p_util.parse_comma_separated_ints(s) == expected)
        s = '1, 2, 3, 4'
        self.assertTrue(p_util.parse_comma_separated_ints(s) == expected)
        s = '1,2, 3,4'
        self.assertTrue(p_util.parse_comma_separated_ints(s) == expected)

    def test_parse_comma_separated_dates(self):
        dates = '2015-01-01,2015-10-23'
        expected = [date(2015, 1, 1), date(2015, 10, 23)]
        ret = p_util.parse_comma_separated_dates(dates)
        self.assertTrue(expected == ret)
        ret = p_util.parse_comma_separated_dates('')
        self.assertTrue([] == ret)

    def test_dates_to_indexes(self):
        dates = [date(2015, 1, 1), date(2015, 1, 23)]
        ret = p_util.dates_to_indexes(date(2015, 1, 1), dates, 4)
        self.assertTrue(ret == [0, 22])
        dates = [date(2015, 1, 31), date(2014, 1, 23), date(2016, 10, 10)]
        ret = p_util.dates_to_indexes(date(2015, 1, 1), dates, 5)
        self.assertTrue(ret == [30])

    def test_standard_deviation_of_diffs(self):
        pairs = [(3, 0), (4, 0), (5, 0), (6, 0), (0, 7)]
        v = p_util.standard_deviation_of_diffs(pairs)
        self.assertTrue(v == sqrt(2.0))
