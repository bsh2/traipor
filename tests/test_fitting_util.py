import csv
import datetime
import unittest
from app.training import fitting_util as f_util


class FittingUtilTestCase(unittest.TestCase):

    csv_content = 'date,60m_critical_power,skiba_bike_score,tss\n' \
                  '02/15/14, 150, 100, 0\n' \
                  '02/16/14, 160, 100, 98.1\n' \
                  '02/16/14, 170, 100, 110.2\n' \
                  '02/17/14, 180, 100, 139.5\n' \
                  '03/01/14, 190, 100, 139.5\n' \
                  '03/29/14, 200, 100, 139.5\n' \
                  '03/01/15, 150, 100, 139.5\n' \
                  '03/29/15, 90, 100, 139.5\n'

    csv_content2 = 'date,60m_critical_power,skiba_bike_score,tss\n' \
                   '01/15/14, 150, 100, 0\n' \
                   '02/15/14, 150, 100, 0\n' \
                   '02/16/14, 160, 100, 98.1\n' \
                   '02/16/14, 170, 100, 110.2\n' \
                   '03/01/14, 190, 100, 139.5\n' \
                   '03/29/14, 200, 100, 139.5\n' \
                   '03/01/15, 150, 100, 139.5\n' \
                   '03/29/15, 90, 100, 139.5\n'

    csv_content3 = 'date,60m_critical_power,tss\n' \
                   '01/15/14, 150, 0\n' \
                   '02/15/14, 150, 0\n' \
                   '02/16/14, 0, 98.1\n' \
                   '02/16/14, 0, 110.2\n' \
                   '03/01/14, 0, 139.5\n' \
                   '03/29/14, 200, 0\n' \
                   '03/01/15, 0, 0\n' \
                   '03/29/15, 90, inf\n'

    def test_calc_rmse(self):
        a = list(range(10))
        b = list(range(10))
        self.assertTrue(f_util.calc_rmse(a, b) == 0)
        b = list(range(1, 11))
        self.assertTrue(f_util.calc_rmse(a, b) == 1)
        b = list(range(11))

    def test_measurement_indexes(self):
        plan = [0, 0, 0, 0, 0, 0, 0]
        self.assertTrue(f_util.measurement_indexes(plan) == [])
        plan = [1, 0, 0, 1, 0, 0, 1]
        self.assertTrue(f_util.measurement_indexes(plan) == [0, 3, 6])

    def test_filter_model_perf_values_2_load_days(self):
        plan = [0, 0, 0, 0, 0, 0, 0]
        model_perfs = [1, 2, 3, 4, 5, 6, 7]
        r = f_util.filter_model_perf_values_2_load_days(plan, model_perfs)
        self.assertTrue(r == [])
        plan = [1, 1, 1, 1, 1, 1, 1]
        r = f_util.filter_model_perf_values_2_load_days(plan, model_perfs)
        self.assertTrue(r == model_perfs)
        plan = [1, 0, 1, 0, 0, 1, 0]
        r = f_util.filter_model_perf_values_2_load_days(plan, model_perfs)
        self.assertTrue(r == [1, 3, 6])

    def test_csv_value_dict_from_iter(self):
        csvlines = FittingUtilTestCase.csv_content.splitlines()
        csvdic = f_util.csv_value_dict_from_iter(csvlines)
        self.assertTrue(len(csvdic['date']) == 8)
        self.assertTrue(len(csvdic['60m_critical_power']) == 8)
        self.assertTrue(len(csvdic['skiba_bike_score']) == 8)

    def test_row_has_must_have_metrics(self):
        csvlines = FittingUtilTestCase.csv_content.splitlines()
        metrics = ['60m_critical_power', 'skiba_bike_score']
        dictreader = csv.DictReader(csvlines)
        for d in dictreader:
            self.assertTrue(f_util.row_has_must_have_metrics(d, metrics))

    def test_row_has_must_have_metrics2(self):
        csvlines = FittingUtilTestCase.csv_content3.splitlines()
        dictreader = csv.DictReader(csvlines)
        metrics = ['60m_critical_power', 'tss']
        row_tests = []
        for d in dictreader:
            row_tests.append(f_util.row_has_must_have_metrics(d, metrics))
        self.assertTrue(row_tests.count(True) == 6)
        self.assertTrue(row_tests.count(False) == 2)

    def test_row_has_must_have_metrics_non_existant_metric(self):
        csvlines = FittingUtilTestCase.csv_content.splitlines()
        dictreader = csv.DictReader(csvlines)
        metrics = ['xxx']
        for d in dictreader:
            with self.assertRaises(KeyError):
                f_util.row_has_must_have_metrics(d, metrics)

    def test_row_has_must_have_metrics_bad_data(self):
        csvlines = FittingUtilTestCase.csv_content.splitlines()
        dictreader = csv.DictReader(csvlines)
        metrics = ['tss']
        row_tests = []
        for d in dictreader:
            row_tests.append(f_util.row_has_must_have_metrics(d, metrics))
        self.assertFalse(all(row_tests))

    def test_accumulate_loads_per_day(self):
        csvlines = FittingUtilTestCase.csv_content.splitlines()
        csvdic = f_util.csv_value_dict_from_iter(csvlines)
        dates = csvdic['date']
        loads = list(map(float, csvdic['skiba_bike_score']))
        acc_loads = f_util.accumulate_loads_per_day(dates, loads)
        self.assertTrue(len(acc_loads) == 7)
        self.assertTrue(acc_loads[1][1] == 200)

    def test_span_best_over_weeks(self):
        csvlines = FittingUtilTestCase.csv_content.splitlines()
        csvdic = f_util.csv_value_dict_from_iter(csvlines)
        dates, loads, perfs = f_util.span_best_over_weeks(csvdic,
                                                          'skiba_bike_score',
                                                          '60m_critical_power')
        self.assertTrue(perfs[0] == 170)
        self.assertTrue(perfs[0] == perfs[1])
        self.assertTrue(perfs[1] == perfs[2])
        self.assertTrue(perfs[3] == 180)

    def test_span_best_over_months(self):
        csvlines = FittingUtilTestCase.csv_content.splitlines()
        csvdic = f_util.csv_value_dict_from_iter(csvlines)
        dates, loads, perfs = f_util.span_best_over_months(csvdic,
                                                           'skiba_bike_score',
                                                           '60m_critical_power')
        self.assertTrue(perfs[0] == 180)
        self.assertTrue(perfs[1] == 180)
        self.assertTrue(perfs[2] == 180)
        self.assertTrue(perfs[3] == 180)
        self.assertTrue(perfs[4] == 200)
        self.assertTrue(perfs[5] == 200)
        self.assertTrue(perfs[6] == 150)
        self.assertTrue(perfs[7] == 150)

    def test_span_best_over_time_frame(self):
        def key_func(x):
            return x[0].year, x[0].month  # group by key (year, month)

        csvlines = FittingUtilTestCase.csv_content.splitlines()
        csvdic = f_util.csv_value_dict_from_iter(csvlines)
        dates = f_util.parse_date_field(csvdic['date'])
        loads = list(map(float, csvdic['skiba_bike_score']))
        perfs = list(map(float, csvdic['60m_critical_power']))
        trainings = zip(dates, loads, perfs)

        dates, loads, perfs = f_util.span_best_over_time_frame(trainings,
                                                               key_func,
                                                               min_group_size=5)
        self.assertTrue(dates == [])
        self.assertTrue(loads == [])
        self.assertTrue(perfs == [])

    def test_span_best_over_time_frame2(self):
        def key_func(x):
            return x[0].year, x[0].month  # group by key (year, month)

        csvlines = FittingUtilTestCase.csv_content2.splitlines()
        csvdic = f_util.csv_value_dict_from_iter(csvlines)
        dates = f_util.parse_date_field(csvdic['date'])
        loads = list(map(float, csvdic['skiba_bike_score']))
        perfs = list(map(float, csvdic['60m_critical_power']))
        trainings = zip(dates, loads, perfs)

        dates, loads, perfs = f_util.span_best_over_time_frame(trainings,
                                                               key_func,
                                                               min_group_size=3)
        self.assertTrue(perfs[0] == 170)
        self.assertTrue(perfs[1] == 170)
        self.assertTrue(perfs[2] == 170)
        self.assertTrue(perfs[3] == 200)
        self.assertTrue(perfs[4] == 200)
        self.assertTrue(perfs[5] == 150)

    def test_collapse_perfs_per_day(self):
        csvlines = FittingUtilTestCase.csv_content.splitlines()
        csvdic = f_util.csv_value_dict_from_iter(csvlines)
        dates, loads, perfs = f_util.span_best_over_weeks(csvdic,
                                                          'skiba_bike_score',
                                                          '60m_critical_power')
        col_perfs = f_util.collapse_perfs_per_day(dates, perfs)
        self.assertTrue(len(col_perfs) == 7)
        expected = [(datetime.date(2014, 2, 15), 170),
                    (datetime.date(2014, 2, 16), 170),
                    (datetime.date(2014, 2, 17), 180),
                    (datetime.date(2014, 3, 1), 190),
                    (datetime.date(2014, 3, 29), 200),
                    (datetime.date(2015, 3, 1), 150),
                    (datetime.date(2015, 3, 29), 90)]
        self.assertTrue(col_perfs == expected)

    def test_normalize_dic_keys(self):
        d = {' foo': 1, 'bar ': 2, ' baz ': 3, 'bla': 4, '': 5}
        expected = {'foo': 1, 'bar': 2, 'baz': 3, 'bla': 4}
        self.assertTrue(f_util.normalize_dic_keys(d) == expected)

    def test_fillup_perf_list_to_plan(self):
        perfs = [10, 20, 30, 40]
        plan = [0.0, 100, 0.0, 0.0, 200, 300, 0.0, 400, 0.0]
        expected = [0.0, 10, 0.0, 0.0, 20, 30, 0.0, 40, 0.0]
        self.assertTrue(f_util.fillup_perf_list_to_plan(perfs, plan) ==
                        expected)

    def test_choose_init_p(self):
        perfs = [0.0, 20, 0.0, 0.0, 20, 10, 0.0, 40, 0.0]
        plan =  [0.0, 100, 0.0, 0.0, 200, 300, 0.0, 400, 0.0]
        expected_p, expected_plan = 10, [300, 0.0, 400, 0.0]
        init_p, plan_since, perfs_since = f_util.choose_init_p(plan, perfs)
        self.assertTrue(init_p == expected_p)
        self.assertTrue(plan_since == expected_plan)

        perfs = [0.0, 20, 0.0, 0.0, 20, 10, 0.0, 5]
        plan = [0.0, 100, 0.0, 0.0, 200, 300, 0.0, 400]
        expected_p, expected_plan = 5, [400]
        init_p, plan_since, perfs_since = f_util.choose_init_p(plan, perfs)
        self.assertTrue(init_p == expected_p)
        self.assertTrue(plan_since == expected_plan)

        perfs = [5]
        plan = [400]
        expected_p, expected_plan = 5, [400]
        init_p, plan_since, perfs_since = f_util.choose_init_p(plan, perfs)
        self.assertTrue(init_p == expected_p)
        self.assertTrue(plan_since == expected_plan)

    def test_date_value_tuples_2_calendar(self):
        date_val_tuples = []
        self.assertTrue(f_util.date_value_tuples_2_calendar(date_val_tuples) == [])
        date_val_tuples.append((datetime.date(2015, 3, 10), 10.1))
        self.assertTrue(f_util.date_value_tuples_2_calendar(date_val_tuples) == [10.1])
        date_val_tuples.append((datetime.date(2015, 3, 10), 12.1))
        date_val_tuples.append((datetime.date(2015, 3, 11), 15.1))
        date_val_tuples.append((datetime.date(2015, 3, 15), 19.1))
        date_val_tuples.append((datetime.date(2015, 3, 16), 29.1))
        date_val_tuples.append((datetime.date(2015, 3, 18), 0.0))
        date_val_tuples.append((datetime.date(2015, 3, 21), 30.0))
        expected = [10.1, 12.1, 15.1, 0.0, 0.0, 0.0, 19.1, 29.1, 0.0, 0.0, 0.0, 0.0, 30.0]
        self.assertTrue(f_util.date_value_tuples_2_calendar(date_val_tuples) == expected)

    def test_plan_perfs_from_dic(self):
        csvlines = FittingUtilTestCase.csv_content.splitlines()
        csvdic = f_util.csv_value_dict_from_iter(csvlines)
        plan, perfs, _, _ = f_util.plan_perfs_from_dic(csvdic, 'tss', '60m_critical_power', True)
        self.assertTrue(len(plan) == len(perfs))
        plan, perfs, _, _ = f_util.plan_perfs_from_dic(csvdic, 'tss', '60m_critical_power', True, 0.3)
        self.assertTrue(len(plan) == len(perfs))


# TODO
# test against empty upload,
#              upload with headers only
#              upload with content lines only
#              missing columns
#              future days
