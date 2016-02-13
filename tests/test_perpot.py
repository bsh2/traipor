import unittest
from app.training import perpot as pp


class PerPotTestCase(unittest.TestCase):

    def test_calc_pp_load_scale_factor(self):
        values = [10, 20, 30, 15, 5]
        self.assertTrue(pp.calc_pp_load_scale_factor(values) == 1/37.5)

    def test_calc_pp_perf_scale_factor(self):
        values = [10, 20, 30, 15, 5]
        self.assertTrue(pp.calc_pp_perf_scale_factor(values) == 1/45)
