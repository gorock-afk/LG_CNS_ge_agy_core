"""생성된 결과 파일의 줄 수·크기를 표로 출력한다 (표준 라이브러리만 사용).

사용법:  python 06_count_output.py agv_hydrogen.html agv_carbon.html
"""

import os
import sys


def measure(path):
    with open(path, "rb") as f:
        data = f.read()
    text = data.decode("utf-8", errors="replace")
    lines = text.splitlines()
    code_lines = [l for l in lines if l.strip()]
    return len(lines), len(code_lines), len(data)


def main(paths):
    if not paths:
        print(__doc__)
        return 1
    print("| 파일 | 전체 줄 | 빈 줄 제외 | 크기(KB) |")
    print("| ---- | ------: | ---------: | -------: |")
    for path in paths:
        if not os.path.isfile(path):
            print("| %s | 파일 없음 | - | - |" % path)
            continue
        total, code, size = measure(path)
        print("| %s | %d | %d | %.1f |" % (os.path.basename(path), total, code, size / 1024.0))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
