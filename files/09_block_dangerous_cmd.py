#!/usr/bin/env python3
"""Antigravity PreToolUse Safety Hook (.agents/hooks.json 연동 예시)."""

import json
import sys

BLOCKED = ("rm -rf", "DROP TABLE", "TRUNCATE TABLE", "git push --force")


def main():
    payload = json.load(sys.stdin)
    cmd = payload.get("toolCall", {}).get("args", {}).get("CommandLine", "")
    for pat in BLOCKED:
        if pat.lower() in cmd.lower():
            print(json.dumps({
                "decision": "deny",
                "reason": f"[보안 가드 차단] 위험 명령어('{pat}') 실행이 정책에 의해 금지되었습니다."
            }, ensure_ascii=False))
            return
    print(json.dumps({"decision": "allow"}))


if __name__ == "__main__":
    main()
