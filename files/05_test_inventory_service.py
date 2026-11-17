"""재고 예약 서비스 검증 테스트 (표준 라이브러리만 사용).

실행:  python 05_test_inventory_service.py
규칙:  이 테스트 파일은 수정하지 않는다. 서비스 코드만 고쳐서 전부 통과시킨다.
"""

import importlib.util
import os
import sys
import threading
import unittest
from decimal import Decimal

_HERE = os.path.dirname(os.path.abspath(__file__))
_TARGET = os.environ.get("INVENTORY_MODULE", os.path.join(_HERE, "05_legacy_inventory_service.py"))
_spec = importlib.util.spec_from_file_location("inventory_service", _TARGET)
inventory = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(inventory)

InventoryService = inventory.InventoryService
InventoryError = inventory.InventoryError


class BasicFlowTest(unittest.TestCase):
    def setUp(self):
        self.svc = InventoryService()
        self.svc.add_stock("BOX-A100", 10, 0.1)

    def test_01_reserve_then_full_release(self):
        rid = self.svc.reserve("req-1", "BOX-A100", 4)
        self.assertEqual(self.svc.stock["BOX-A100"], 6)
        self.assertEqual(self.svc.release(rid), 0)
        self.assertEqual(self.svc.stock["BOX-A100"], 10)

    def test_02_reserve_more_than_stock_is_rejected(self):
        with self.assertRaises(InventoryError):
            self.svc.reserve("req-2", "BOX-A100", 11)
        self.assertEqual(self.svc.stock["BOX-A100"], 10)


class ConcurrencyTest(unittest.TestCase):
    def test_03_concurrent_reserve_never_oversells(self):
        svc = InventoryService()
        svc.add_stock("BOX-A100", 10, 0.1)
        reservation_ids, failures = [], []
        guard = threading.Lock()

        def worker(n):
            try:
                rid = svc.reserve("req-%d" % n, "BOX-A100", 1)
                with guard:
                    reservation_ids.append(rid)
            except InventoryError:
                with guard:
                    failures.append(n)

        threads = [threading.Thread(target=worker, args=(n,)) for n in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(reservation_ids), 10, "재고 10개에 정확히 10건만 예약되어야 한다")
        self.assertEqual(len(failures), 40)
        self.assertEqual(svc.stock["BOX-A100"], 0)
        self.assertEqual(len(set(reservation_ids)), 10, "예약 ID는 서로 달라야 한다")

    def test_04_same_request_id_is_idempotent(self):
        svc = InventoryService()
        svc.add_stock("BOX-A100", 10, 0.1)
        first = svc.reserve("req-retry", "BOX-A100", 3)
        second = svc.reserve("req-retry", "BOX-A100", 3)
        self.assertEqual(first, second, "같은 request_id 재시도는 같은 예약을 돌려줘야 한다")
        self.assertEqual(svc.stock["BOX-A100"], 7)


class ReleaseValidationTest(unittest.TestCase):
    def setUp(self):
        self.svc = InventoryService()
        self.svc.add_stock("BOX-A100", 10, 0.1)
        self.rid = self.svc.reserve("req-1", "BOX-A100", 4)

    def test_05_partial_release(self):
        self.assertEqual(self.svc.release(self.rid, 1), 3)
        self.assertEqual(self.svc.stock["BOX-A100"], 7)

    def test_06_release_more_than_reserved_is_rejected(self):
        with self.assertRaises(InventoryError):
            self.svc.release(self.rid, 5)
        self.assertEqual(self.svc.stock["BOX-A100"], 6)

    def test_07_release_non_positive_is_rejected(self):
        for bad in (0, -3):
            with self.assertRaises(InventoryError):
                self.svc.release(self.rid, bad)
        self.assertEqual(self.svc.stock["BOX-A100"], 6)


class WeightTest(unittest.TestCase):
    def test_08_total_weight_is_exact(self):
        svc = InventoryService()
        svc.add_stock("BOX-A100", 10, 0.1)
        svc.add_stock("BOX-B200", 10, 0.2)
        total = svc.total_weight([("BOX-A100", 1), ("BOX-B200", 1)])
        self.assertEqual(Decimal(str(total)), Decimal("0.3"), "0.1kg + 0.2kg 는 정확히 0.3kg")
        self.assertEqual(Decimal(str(svc.total_weight([("BOX-A100", 3)]))), Decimal("0.3"))


class SearchTest(unittest.TestCase):
    def setUp(self):
        self.svc = InventoryService()
        self.svc.add_stock("BOX-A100", 12, 0.1)
        self.svc.add_stock("BOX-B200", 3, 0.2)
        self.svc.add_stock("PAL-C300", 40, 9.5)

    def tearDown(self):
        if hasattr(sys, "workshop_pwned"):
            delattr(sys, "workshop_pwned")

    def test_09_valid_filters(self):
        self.assertEqual(self.svc.search("qty >= 10"), ["BOX-A100", "PAL-C300"])
        self.assertEqual(self.svc.search("sku == 'BOX-B200'"), ["BOX-B200"])
        self.assertEqual(self.svc.search("qty > 0 and qty < 5"), ["BOX-B200"])
        self.assertEqual(self.svc.search("qty < 5 or sku == 'PAL-C300'"), ["BOX-B200", "PAL-C300"])

    def test_10_filter_rejects_code_execution(self):
        payload = "__import__('builtins').setattr(__import__('sys'), 'workshop_pwned', True) or True"
        with self.assertRaises(InventoryError):
            self.svc.search(payload)
        self.assertFalse(hasattr(sys, "workshop_pwned"), "필터 문자열이 코드로 실행되면 안 된다")
        for bad in ("qty.__class__", "open('x')", "sku + 1", "qty >= 10; qty"):
            with self.assertRaises(InventoryError):
                self.svc.search(bad)


if __name__ == "__main__":
    unittest.main(verbosity=2)
