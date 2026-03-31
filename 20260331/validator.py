#!/usr/bin/env python3
"""
할루시네이션 교차 검증기
- 문제 은행의 모든 문항을 검사하고 신뢰도/출처 리포트를 생성합니다.
"""

import io
import json
import sys
from pathlib import Path

# Windows 터미널 UTF-8 출력 설정
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

QUESTIONS_FILE = Path(__file__).parent / "questions.json"
CONFIDENCE_THRESHOLD = 0.7
REQUIRED_FIELDS = {"id", "category", "difficulty", "question", "choices",
                   "answer", "explanation", "source", "confidence"}


def validate_question(q: dict) -> list[str]:
    """단일 문항의 문제점을 반환합니다."""
    issues = []

    # 필수 필드 검사
    missing = REQUIRED_FIELDS - q.keys()
    if missing:
        issues.append(f"필수 필드 누락: {missing}")

    # 선택지 수 검사
    if len(q.get("choices", [])) != 5:
        issues.append(f"선택지 수 오류: {len(q.get('choices', []))}개 (5개 필요)")

    # 정답 인덱스 검사
    answer = q.get("answer", -1)
    if not (0 <= answer < len(q.get("choices", []))):
        issues.append(f"정답 인덱스 {answer} 범위 초과")

    # 신뢰도 검사
    conf = q.get("confidence", -1)
    if not (0.0 <= conf <= 1.0):
        issues.append(f"신뢰도 {conf} 범위 오류 (0.0~1.0)")
    elif conf < CONFIDENCE_THRESHOLD:
        issues.append(f"⚠️  낮은 신뢰도 ({conf:.0%}) — 교차 검증 필요")

    # 출처 검사
    if not q.get("source", "").strip():
        issues.append("출처(source) 비어 있음")

    # 설명 검사
    if len(q.get("explanation", "")) < 10:
        issues.append("해설이 너무 짧음 (10자 이상 권장)")

    return issues


def run_validation() -> dict:
    """전체 문제 은행 검증 리포트를 반환합니다."""
    with open(QUESTIONS_FILE, encoding="utf-8") as f:
        data = json.load(f)

    questions = data["questions"]
    report = {
        "total": len(questions),
        "passed": 0,
        "warnings": 0,
        "errors": 0,
        "details": [],
    }

    for q in questions:
        issues = validate_question(q)
        errors = [i for i in issues if not i.startswith("⚠️")]
        warnings = [i for i in issues if i.startswith("⚠️")]

        status = "✅ OK" if not issues else ("⚠️  WARN" if not errors else "❌ ERROR")
        report["details"].append({
            "id": q.get("id"),
            "question_preview": q.get("question", "")[:40],
            "status": status,
            "issues": issues,
        })

        if not issues:
            report["passed"] += 1
        elif errors:
            report["errors"] += 1
        else:
            report["warnings"] += 1

    return report


def print_report(report: dict) -> None:
    """검증 리포트를 콘솔에 출력합니다."""
    print("\n" + "="*60)
    print("  할루시네이션 교차 검증 리포트")
    print("="*60)
    print(f"  전체 문항: {report['total']}개")
    print(f"  ✅ 통과:   {report['passed']}개")
    print(f"  ⚠️  경고:   {report['warnings']}개  (낮은 신뢰도 — 검토 권장)")
    print(f"  ❌ 오류:   {report['errors']}개  (수정 필요)")
    print("-"*60)

    for d in report["details"]:
        if d["issues"]:
            print(f"\n  Q{d['id']:02d}: {d['status']}")
            print(f"       {d['question_preview']}...")
            for issue in d["issues"]:
                print(f"       → {issue}")

    print("\n" + "="*60)
    print("  교차 검증 가이드라인")
    print("="*60)
    print("""
  [1] 신뢰도(confidence) 기준
      - 0.9 이상  : 공신력 있는 문헌/공식 데이터로 확인된 사실
      - 0.7~0.9   : 일반적으로 통용되나 세부 사항 이견 가능
      - 0.7 미만  : 논쟁 중이거나 AI가 생성한 미검증 정보
                    → 반드시 1차 자료로 교차 검증 필요

  [2] 출처(source) 작성 원칙
      - 구체적인 문헌명/기관명 명시
      - "Wikipedia" 단독은 허용하지 않음
      - 가능하면 2개 이상의 독립 출처 기재

  [3] AI 할루시네이션 방지 체크리스트
      □ 수치(날짜, 거리, 크기 등)를 공식 자료로 재확인했는가?
      □ 고유명사(인명, 지명)의 표기가 정확한가?
      □ 정답이 선택지 중 단 하나만 맞는가?
      □ 해설이 정답을 논리적으로 뒷받침하는가?
      □ 낮은 신뢰도 문항에 [검증 필요] 태그를 붙였는가?

  [4] 검증 절차
      1) AI 생성 문항 작성
      2) validator.py 실행으로 구조적 오류 확인
      3) 신뢰도 < 0.7 문항 수동 교차 검증
      4) 2개 이상의 독립 출처로 사실 확인
      5) 검증 완료 후 confidence 점수 업데이트
""")


if __name__ == "__main__":
    report = run_validation()
    print_report(report)

    if report["errors"] > 0:
        print(f"  ❌ {report['errors']}개 오류가 있습니다. questions.json을 수정하세요.\n")
        raise SystemExit(1)
    elif report["warnings"] > 0:
        print(f"  ⚠️  {report['warnings']}개 문항을 교차 검증하세요.\n")
    else:
        print("  ✅ 모든 문항이 검증 기준을 통과했습니다.\n")
