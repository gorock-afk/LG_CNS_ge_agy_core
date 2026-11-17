# Antigravity 실습 파일

압축을 푼 폴더를 Antigravity 에서 프로젝트(워크스페이스)로 엽니다.
모든 파일은 외부 라이브러리 설치 없이 동작합니다. (Python 3.9 이상, Chrome 144 이상)

| 파일 | 쓰는 곳 | 내용 |
| ---- | ------- | ---- |
| `01_buggy_wms_board.html` | Part 1 | 결함 7건이 숨은 입출고 작업 보드. `자가 테스트 실행` 버튼이 `ALL PASS (7/7)` 가 되면 완료 |
| `02_3d_single_prompt.md` | Part 2 | 단일 프롬프트 3D·물리 과제와 채점표 |
| `03_service_call_graph.csv` · `03_graph_questions.md` | Part 2 | 서비스 240개 · 호출 877건 의존성 그래프와 4문항 |
| `04_wms_console_blueprint.png` | Part 2 | 출고 승인 콘솔 화면 설계도와 업무 규칙 R1~R5 |
| `05_legacy_inventory_service.py` · `05_test_inventory_service.py` | Part 2 · 3 | 결함 6건이 숨은 재고 예약 서비스와 테스트 10개 (처음엔 6개 실패) |
| `06_compare_scorecard.md` · `06_count_output.py` | Part 2 | 모델 비교 기록표, 결과 파일 줄 수 측정 도구 |
| `07_team_rule_example.md` | Part 3 | `.agents/rules/` 에 저장되는 팀 규칙 예시 |

## 빠른 확인

```text
python 05_test_inventory_service.py      # 처음 실행: FAILED (failures=6)
```

`01_buggy_wms_board.html` 을 Chrome 으로 열고 `자가 테스트 실행` 을 누르면 `7 FAIL / 7` 이 보입니다.

## 지켜야 할 것
- `01` 의 자가 테스트 블록과 `05_test_inventory_service.py` 는 수정하지 않습니다.
- 모델 비교는 모델마다 새 대화에서 시작합니다.
