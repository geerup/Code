import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from metrics import Counter, Gauge, Histogram, Registry  # noqa: E402


class TestCounter(unittest.TestCase):
    def test_inc(self):
        c = Counter()
        c.inc(); c.inc(3)
        self.assertEqual(c.value, 4)

    def test_no_decrease(self):
        with self.assertRaises(ValueError):
            Counter().inc(-1)


class TestGauge(unittest.TestCase):
    def test_set_inc_dec(self):
        g = Gauge()
        g.set(10); g.inc(5); g.dec(3)
        self.assertEqual(g.value, 12)


class TestHistogram(unittest.TestCase):
    def test_count_and_avg(self):
        h = Histogram([10, 100])
        for v in (5, 15, 50):
            h.observe(v)
        self.assertEqual(h.count, 3)
        self.assertAlmostEqual(h.avg, 70 / 3)

    def test_bucketing(self):
        h = Histogram([10, 100])
        h.observe(5)    # <=10
        h.observe(50)   # <=100
        h.observe(500)  # +Inf
        self.assertEqual(h.counts, [1, 1])
        self.assertEqual(h.inf, 1)

    def test_quantile_estimation(self):
        h = Histogram([10, 50, 100])
        for _ in range(90):
            h.observe(5)    # bucket <=10
        for _ in range(10):
            h.observe(80)   # bucket <=100
        self.assertEqual(h.quantile(0.5), 10)   # median in first bucket
        self.assertEqual(h.quantile(0.95), 100) # tail in last bucket

    def test_empty_quantile(self):
        self.assertEqual(Histogram().quantile(0.5), 0.0)


class TestRegistry(unittest.TestCase):
    def setUp(self):
        self.reg = Registry()
        self.reg.counter("http_requests_total").inc(5)
        self.reg.gauge("in_flight").set(2)
        h = self.reg.histogram("latency_ms", [10, 100])
        for v in (5, 20, 200):
            h.observe(v)

    def test_same_name_returns_same_metric(self):
        self.assertIs(self.reg.counter("http_requests_total"),
                      self.reg.counters["http_requests_total"])

    def test_json_shape(self):
        j = self.reg.to_json()
        self.assertEqual(j["counters"]["http_requests_total"], 5)
        self.assertEqual(j["gauges"]["in_flight"], 2)
        self.assertEqual(j["histograms"]["latency_ms"]["count"], 3)

    def test_prometheus_format(self):
        text = self.reg.render_prometheus()
        self.assertIn("# TYPE http_requests_total counter", text)
        self.assertIn("http_requests_total 5", text)
        self.assertIn('latency_ms_bucket{le="+Inf"}', text)
        self.assertIn("latency_ms_count 3", text)


if __name__ == "__main__":
    unittest.main()
