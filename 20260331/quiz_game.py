#!/usr/bin/env python3
"""상식 퀴즈 게임"""

import json
import random
import sys
from datetime import datetime
from pathlib import Path

# Windows 터미널 한글 깨짐 방지
sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).parent
QUESTIONS_FILE = BASE_DIR / "questions.json"
RANKINGS_FILE = BASE_DIR / "rankings.json"

CATEGORIES = ["한국사", "과학", "지리", "일반상식"]

ENCOURAGEMENTS = [
    "훌륭해요!",
    "완벽합니다!",
    "대단해요!",
    "맞아요, 잘 알고 있네요!",
    "정확합니다!",
]


def load_questions(category: str = None) -> list:
    with open(QUESTIONS_FILE, encoding="utf-8") as f:
        data = json.load(f)
    questions = data["questions"]
    if category:
        questions = [q for q in questions if q["category"] == category]
    return questions


def get_grade(score: int) -> tuple:
    """점수에 따른 등급과 메시지를 반환합니다."""
    if score >= 380:
        return "S", "완벽해요! 상식왕!"
    elif score >= 300:
        return "A", "훌륭해요!"
    elif score >= 200:
        return "B", "괜찮아요!"
    elif score >= 100:
        return "C", "조금 더 공부해요!"
    else:
        return "D", "다시 도전해보세요!"


def display_question(q: dict, num: int, total: int) -> None:
    print(f"\n{'='*55}")
    print(f"  문제 {num}/{total}  [{q['category']}]")
    print(f"{'='*55}")
    print(f"\n  {q['question']}\n")
    for i, choice in enumerate(q["choices"]):
        print(f"  {i + 1}. {choice}")


def get_user_answer(num_choices: int) -> int:
    """사용자 입력을 받아 0-based 인덱스로 반환합니다."""
    while True:
        try:
            raw = input(f"\n  정답 입력 (1~{num_choices}): ").strip()
            val = int(raw)
            if 1 <= val <= num_choices:
                return val - 1
            print(f"  1~{num_choices} 사이 숫자를 입력하세요.")
        except ValueError:
            print("  숫자를 입력하세요.")
        except KeyboardInterrupt:
            print("\n\n  게임을 종료합니다.")
            sys.exit(0)


def show_feedback(q: dict, user_answer: int) -> bool:
    """정답/오답 피드백을 출력하고 정답 여부를 반환합니다."""
    correct = user_answer == q["answer"]
    if correct:
        print(f"\n  ✅ 정답입니다! {random.choice(ENCOURAGEMENTS)}")
    else:
        correct_text = q["choices"][q["answer"]]
        print(f"\n  ❌ 오답입니다. 정답은 [{correct_text}]")
        print(f"  💡 해설: {q['explanation']}")
    return correct


def save_ranking(nickname: str, score: int, grade: str) -> None:
    """결과를 rankings.json에 저장합니다."""
    rankings = []
    if RANKINGS_FILE.exists():
        with open(RANKINGS_FILE, encoding="utf-8") as f:
            rankings = json.load(f)

    rankings.append({
        "nickname": nickname,
        "score": score,
        "grade": grade,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })

    with open(RANKINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(rankings, f, ensure_ascii=False, indent=2)


def show_rankings() -> None:
    """상위 10명 랭킹을 출력합니다."""
    if not RANKINGS_FILE.exists():
        print("\n  저장된 랭킹이 없습니다.")
        return

    with open(RANKINGS_FILE, encoding="utf-8") as f:
        rankings = json.load(f)

    top10 = sorted(rankings, key=lambda x: x["score"], reverse=True)[:10]

    print(f"\n{'='*55}")
    print("  🏆 상위 10명 랭킹")
    print(f"{'='*55}")
    print(f"  {'순위':<4} {'닉네임':<12} {'점수':<6} {'등급':<4} {'날짜'}")
    print(f"  {'-'*50}")
    for i, r in enumerate(top10, 1):
        print(f"  {i:<4} {r['nickname']:<12} {r['score']:<6} {r['grade']:<4} {r['date']}")
    print()


def run_game(nickname: str, category: str = None) -> None:
    """게임을 진행합니다."""
    questions = load_questions(category)
    if not questions:
        print("  해당 카테고리의 문제가 없습니다.")
        return

    random.shuffle(questions)
    total = len(questions)
    correct_count = 0

    label = category if category else "전체 랜덤"
    print(f"\n  [{label}] 모드 — 총 {total}문제 시작!\n")

    for i, q in enumerate(questions, 1):
        display_question(q, i, total)
        user_answer = get_user_answer(len(q["choices"]))
        if show_feedback(q, user_answer):
            correct_count += 1
        if i < total:
            try:
                input("\n  [Enter]로 다음 문제...")
            except KeyboardInterrupt:
                print("\n\n  게임을 종료합니다.")
                sys.exit(0)

    score = correct_count * 10
    grade, message = get_grade(score)

    print(f"\n{'='*55}")
    print(f"  🎯 게임 종료!")
    print(f"  정답: {correct_count}/{total}  점수: {score}점")
    print(f"  등급: {grade}  —  {message}")
    print(f"{'='*55}\n")

    save_ranking(nickname, score, grade)
    print(f"  결과가 저장되었습니다. (닉네임: {nickname})\n")


def main() -> None:
    print("\n" + "=" * 55)
    print("        🧠 상식 퀴즈 게임에 오신 것을 환영합니다!")
    print("=" * 55)

    try:
        nickname = input("\n  닉네임을 입력하세요: ").strip()
        if not nickname:
            nickname = "익명"

        print("\n  모드를 선택하세요:")
        print("  1. 전체 랜덤")
        print("  2. 카테고리 선택")
        print("  3. 랭킹 조회")
        print("  4. 종료")

        choice = input("\n  선택 (1~4): ").strip()

        if choice == "1":
            run_game(nickname)
        elif choice == "2":
            print("\n  카테고리:")
            for i, cat in enumerate(CATEGORIES, 1):
                print(f"  {i}. {cat}")
            cat_input = input("\n  카테고리 번호 입력 (1~4): ").strip()
            try:
                cat_idx = int(cat_input) - 1
                if 0 <= cat_idx < len(CATEGORIES):
                    run_game(nickname, CATEGORIES[cat_idx])
                else:
                    print("  올바른 번호를 입력하세요.")
            except ValueError:
                print("  숫자를 입력하세요.")
        elif choice == "3":
            show_rankings()
        elif choice == "4":
            print("\n  종료합니다. 다음에 또 도전하세요!")
        else:
            print("  올바른 번호를 입력하세요.")

    except KeyboardInterrupt:
        print("\n\n  종료합니다.")


if __name__ == "__main__":
    main()
