#!/usr/bin/env python3
"""상식 퀴즈 게임 - 할루시네이션 방지 기능 포함"""

import json
import os
import random
import time
from datetime import datetime
from pathlib import Path


CONFIDENCE_THRESHOLD = 0.7
QUESTIONS_FILE = Path(__file__).parent / "questions.json"
RESULTS_DIR = Path(__file__).parent / "results"


def load_questions(category: str = None, difficulty: str = None) -> list[dict]:
    """문제 은행에서 문제를 불러옵니다."""
    with open(QUESTIONS_FILE, encoding="utf-8") as f:
        data = json.load(f)

    questions = data["questions"]

    if category:
        questions = [q for q in questions if q["category"] == category]
    if difficulty:
        questions = [q for q in questions if q["difficulty"] == difficulty]

    return questions


def display_question(q: dict, num: int, total: int) -> None:
    """문제를 화면에 출력합니다."""
    print(f"\n{'='*60}")
    print(f"문제 {num}/{total}  [{q['category']}] 난이도: {q['difficulty']}")

    # 낮은 신뢰도 경고
    if q["confidence"] < CONFIDENCE_THRESHOLD:
        print(f"  ⚠️  [검증 필요] 신뢰도: {q['confidence']:.0%}")
    else:
        print(f"  ✓  신뢰도: {q['confidence']:.0%} | 출처: {q['source'][:40]}...")

    print(f"\n{q['question']}\n")

    for i, choice in enumerate(q["choices"]):
        print(f"  {i+1}. {choice}")


def get_user_answer(num_choices: int) -> int:
    """사용자 입력을 받아 0-based 인덱스로 반환합니다."""
    while True:
        try:
            raw = input(f"\n정답 입력 (1~{num_choices}): ").strip()
            val = int(raw)
            if 1 <= val <= num_choices:
                return val - 1
            print(f"1~{num_choices} 사이 숫자를 입력하세요.")
        except ValueError:
            print("숫자를 입력하세요.")
        except KeyboardInterrupt:
            print("\n\n게임을 종료합니다.")
            raise SystemExit(0)


def show_result(q: dict, user_answer: int, elapsed: float) -> bool:
    """정답/오답 결과를 표시하고 정답 여부를 반환합니다."""
    correct = user_answer == q["answer"]
    if correct:
        print(f"\n  ✅ 정답! ({elapsed:.1f}초)")
    else:
        print(f"\n  ❌ 오답! 정답: {q['choices'][q['answer']]} ({elapsed:.1f}초)")
    print(f"  💡 {q['explanation']}")
    return correct


def save_result(results: dict) -> Path:
    """게임 결과를 JSON 파일로 저장합니다."""
    RESULTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = RESULTS_DIR / f"result_{timestamp}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    return path


def show_final_score(score: int, total: int, details: list[dict]) -> None:
    """최종 점수 및 요약을 표시합니다."""
    pct = score / total * 100 if total else 0
    print(f"\n{'='*60}")
    print(f"  최종 점수: {score}/{total} ({pct:.0f}%)")

    if pct >= 80:
        grade = "S (완벽해요!)"
    elif pct >= 60:
        grade = "A (잘했어요!)"
    elif pct >= 40:
        grade = "B (괜찮아요!)"
    else:
        grade = "C (더 공부해요!)"
    print(f"  등급: {grade}")

    # 낮은 신뢰도 문항 안내
    low_conf = [d for d in details if d["confidence"] < CONFIDENCE_THRESHOLD]
    if low_conf:
        print(f"\n  ⚠️  검증 필요 문항 {len(low_conf)}개:")
        for d in low_conf:
            print(f"    - Q{d['id']}: {d['question'][:30]}... (신뢰도 {d['confidence']:.0%})")
    print(f"{'='*60}\n")


def select_questions(all_questions: list[dict], count: int = 5) -> list[dict]:
    """문제를 랜덤으로 선택합니다."""
    return random.sample(all_questions, min(count, len(all_questions)))


def run_game(category: str = None, difficulty: str = None, count: int = 5) -> None:
    """메인 게임 루프입니다."""
    print("\n" + "="*60)
    print("    🎯 상식 퀴즈 게임")
    print("    (Ctrl+C로 언제든지 종료)")
    print("="*60)

    all_questions = load_questions(category, difficulty)
    if not all_questions:
        print("해당 조건의 문제가 없습니다.")
        return

    questions = select_questions(all_questions, count)
    total = len(questions)
    score = 0
    details = []

    for i, q in enumerate(questions, 1):
        display_question(q, i, total)
        start = time.time()
        user_answer = get_user_answer(len(q["choices"]))
        elapsed = time.time() - start

        correct = show_result(q, user_answer, elapsed)
        if correct:
            score += 1

        details.append({
            "id": q["id"],
            "question": q["question"],
            "category": q["category"],
            "difficulty": q["difficulty"],
            "user_answer": q["choices"][user_answer],
            "correct_answer": q["choices"][q["answer"]],
            "is_correct": correct,
            "elapsed_seconds": round(elapsed, 2),
            "confidence": q["confidence"],
            "source": q["source"],
        })

        if i < total:
            input("\n  [Enter]로 다음 문제...")

    show_final_score(score, total, details)

    result_data = {
        "played_at": datetime.now().isoformat(),
        "category": category or "전체",
        "difficulty": difficulty or "전체",
        "score": score,
        "total": total,
        "percentage": round(score / total * 100, 1) if total else 0,
        "details": details,
    }
    path = save_result(result_data)
    print(f"  결과 저장: {path}\n")


def show_history() -> None:
    """이전 게임 기록을 조회합니다."""
    if not RESULTS_DIR.exists() or not list(RESULTS_DIR.glob("*.json")):
        print("저장된 기록이 없습니다.")
        return

    files = sorted(RESULTS_DIR.glob("*.json"), reverse=True)[:10]
    print(f"\n{'='*60}")
    print("  최근 게임 기록 (최대 10개)")
    print(f"{'='*60}")
    for f in files:
        with open(f, encoding="utf-8") as fp:
            r = json.load(fp)
        dt = r["played_at"][:16].replace("T", " ")
        print(f"  {dt} | {r['category']} | {r['difficulty']} | {r['score']}/{r['total']} ({r['percentage']}%)")
    print()


def main() -> None:
    """진입점 - 메뉴 표시 및 게임 시작"""
    print("\n========================================")
    print("       상식 퀴즈 게임에 오신 것을 환영합니다!")
    print("========================================")
    print("1. 게임 시작 (전체)")
    print("2. 카테고리 선택")
    print("3. 난이도 선택")
    print("4. 기록 조회")
    print("5. 종료")

    try:
        choice = input("\n선택: ").strip()
    except KeyboardInterrupt:
        print("\n종료합니다.")
        return

    if choice == "1":
        run_game()
    elif choice == "2":
        print("\n카테고리: 역사 / 과학 / 지리 / 문화")
        cat = input("카테고리 입력: ").strip()
        run_game(category=cat)
    elif choice == "3":
        print("\n난이도: 쉬움 / 보통 / 어려움")
        diff = input("난이도 입력: ").strip()
        run_game(difficulty=diff)
    elif choice == "4":
        show_history()
    elif choice == "5":
        print("종료합니다.")
    else:
        print("올바른 선택을 입력하세요.")


if __name__ == "__main__":
    main()
