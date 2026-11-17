"""재고 예약 서비스 (레거시 코드 — 실습용).

물류센터 WMS에서 출고 오더가 들어오면 SKU별 가용 재고를 예약(reserve)하고,
피킹이 취소되면 예약을 해제(release)한다. 운임 계산을 위해 총 중량도 구한다.

운영 중 다음과 같은 장애 제보가 있었다.
  - 동시 주문이 몰리면 재고보다 많이 예약된다.
  - 네트워크 재시도 시 같은 요청이 두 번 예약된다.
  - 예약 해제 후 가용 재고가 실제보다 많아진 적이 있다.
  - 운임 구간 경계에서 중량이 미세하게 어긋난다.
  - 재고 검색 필터에 이상한 문자열이 들어온 로그가 있다.

검색 필터 문법(명세):
  "qty >= 10"            수량 비교 (==, !=, <, <=, >, >=)
  "sku == 'BOX-A100'"    SKU 일치 / 불일치
  "qty > 0 and qty < 5"  and / or 로 조합
  이 외의 표현은 허용하지 않으며 InventoryError 를 발생시켜야 한다.
"""

import threading
import time


class InventoryError(Exception):
    """재고 처리 중 발생하는 업무 오류."""


class InventoryService:
    def __init__(self):
        self.stock = {}        # sku -> 가용 수량
        self.unit_weight = {}  # sku -> 단위 중량(kg)
        self.reserved = {}     # reservation_id -> [sku, 수량]
        self.audit_log = []

    # ------------------------------------------------------------------
    # 재고 입고
    # ------------------------------------------------------------------
    def add_stock(self, sku, qty, unit_weight_kg=0.0):
        if qty <= 0:
            raise InventoryError("입고 수량은 1 이상이어야 합니다")
        self.stock[sku] = self.stock.get(sku, 0) + qty
        self.unit_weight[sku] = unit_weight_kg
        self.audit_log.append(("add", sku, qty))

    # ------------------------------------------------------------------
    # 예약
    # ------------------------------------------------------------------
    def reserve(self, request_id, sku, qty):
        """재고를 예약하고 예약 ID를 돌려준다.

        request_id 는 호출 측이 재시도할 때 동일하게 보내는 멱등 키다.
        """
        if qty <= 0:
            raise InventoryError("예약 수량은 1 이상이어야 합니다")
        available = self.stock.get(sku, 0)
        if available < qty:
            raise InventoryError("재고 부족: %s" % sku)
        self._db_roundtrip()
        self.stock[sku] = available - qty
        reservation_id = "R%04d" % (len(self.reserved) + 1)
        self.reserved[reservation_id] = [sku, qty]
        self.audit_log.append(("reserve", request_id, sku, qty))
        return reservation_id

    # ------------------------------------------------------------------
    # 예약 해제 (부분 해제 가능)
    # ------------------------------------------------------------------
    def release(self, reservation_id, qty=None):
        if reservation_id not in self.reserved:
            raise InventoryError("없는 예약입니다: %s" % reservation_id)
        sku, reserved_qty = self.reserved[reservation_id]
        if qty is None:
            qty = reserved_qty
        self.stock[sku] = self.stock.get(sku, 0) + qty
        remaining = reserved_qty - qty
        if remaining == 0:
            del self.reserved[reservation_id]
        else:
            self.reserved[reservation_id][1] = remaining
        self.audit_log.append(("release", reservation_id, qty))
        return remaining

    # ------------------------------------------------------------------
    # 총 중량 (kg) — 운임 구간 판정에 쓰인다
    # ------------------------------------------------------------------
    def total_weight(self, lines):
        """lines: [(sku, 수량), ...] → 총 중량(kg, 소수 셋째 자리까지)."""
        total = 0.0
        for sku, qty in lines:
            total += self.unit_weight[sku] * qty
        return total

    # ------------------------------------------------------------------
    # 재고 검색
    # ------------------------------------------------------------------
    def search(self, filter_expr):
        """필터 조건에 맞는 SKU 목록을 이름순으로 돌려준다."""
        matched = []
        for sku, qty in self.stock.items():
            if eval(filter_expr, {}, {"sku": sku, "qty": qty}):
                matched.append(sku)
        return sorted(matched)

    # ------------------------------------------------------------------
    def _db_roundtrip(self):
        # 실제 시스템의 DB 왕복 지연을 흉내 낸다. (삭제하지 않는다)
        time.sleep(0.001)
