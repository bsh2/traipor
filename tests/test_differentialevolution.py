import unittest
from app.training import differentialevolution as de


class DifferentialEvolutionTestCase(unittest.TestCase):

    def test_generate_individual(self):
        off_days = list(range(3 * 7))
        i = de.generate_individual(3, off_days, 1.0, 0.0, 1)
        self.assertTrue(len(i) == 3 * 7)
        self.assertTrue(list(i) == [0.0] * (3 * 7))

        off_days = []
        i = de.generate_individual(3, off_days, 100, 0.0, 1)
        self.assertTrue(max(i) <= 100)
        i = de.generate_individual(3, off_days, 100, 0.0, 2)
        self.assertTrue(max(i) <= 100 / 2)
        i = de.generate_individual(3, off_days, 100, 0.0, 4)
        self.assertTrue(max(i) <= 100 / 4)
        i = de.generate_individual(3, off_days, 100, 50, 4)
        self.assertTrue(min(i) >=  50)
        i = de.generate_individual(3, off_days, 100, 100, 4)
        self.assertTrue(all([v == 100 for v in i]))
        off_days = [1, 10, 15]
        i = de.generate_individual(3, off_days, 100, 10, 4)
        for d in off_days:
            self.assertTrue(i[d] == 0.0)

    def test_de_operator(self):
        a = [100, 100, 200, 0, 50, 25, 0]
        b = [100, 100, 200, 0, 50, 25, 0]
        c = [100, 100, 200, 0, 50, 25, 0]
        d = [100, 100, 200, 0, 50, 25, 0]
        m = de.de_operator(a, b, c, d, 200, 15, 0.7, 0.9)
        self.assertTrue(m[3] == 0.0)
        self.assertTrue(m[6] == 0.0)
