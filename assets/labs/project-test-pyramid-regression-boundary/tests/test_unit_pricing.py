import unittest

from test_pyramid_demo import OrderLine, parse_order_row, summarize_orders


class UnitPricingTests(unittest.TestCase):
    def test_discount_rounds_to_nearest_cent(self):
        line = OrderLine("o-1", "alice", "pen", 99, 3, 10)
        self.assertEqual(line.gross_cents, 297)
        self.assertEqual(line.discount_cents, 30)
        self.assertEqual(line.net_cents, 267)

    def test_parse_rejects_zero_quantity(self):
        with self.assertRaisesRegex(ValueError, "quantity"):
            parse_order_row(
                {
                    "order_id": "o-1",
                    "customer": "alice",
                    "item": "pen",
                    "unit_price_cents": "99",
                    "quantity": "0",
                    "discount_pct": "0",
                },
                2,
            )

    def test_summary_chooses_top_customer_with_stable_tie_breaker(self):
        lines = [
            OrderLine("o-1", "bob", "a", 100, 1, 0),
            OrderLine("o-2", "alice", "b", 100, 1, 0),
        ]
        summary = summarize_orders(lines)
        self.assertEqual(summary["top_customer"], "alice")


if __name__ == "__main__":
    unittest.main()
