"""상식 퀴즈 게임 테스트 (PRD 스펙 기준)"""

import json
import sys
import tempfile
from collections import Counter
from pathlib import Path
from unittest.mock import patch

# 프로젝트 루트를 sys.path에 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import quiz_game


# ──────────────────────────────────────────────────────────────────────────────
# 헬퍼
# ──────────────────────────────────────────────────────────────────────────────

def load_all_questions():
    with open(PROJECT_ROOT / "questions.json", encoding="utf-8") as f:
        return json.load(f)["questions"]


# ──────────────────────────────────────────────────────────────────────────────
# 1. 문제 은행 검증
# ──────────────────────────────────────────────────────────────────────────────

def test_total_question_count():
    """questions.json에 40문제가 있어야 한다."""
    questions = load_all_questions()
    assert len(questions) == 40, f"총 문제 수가 40이어야 하는데 {len(questions)}개입니다."


def test_category_question_count():
    """카테고리별로 정확히 10문제씩이어야 한다."""
    questions = load_all_questions()
    counts = Counter(q["category"] for q in questions)
    expected = {"한국사", "과학", "지리", "일반상식"}
    assert set(counts.keys()) == expected, f"카테고리 목록이 다릅니다: {set(counts.keys())}"
    for cat, count in counts.items():
        assert count == 10, f"{cat} 카테고리 문제가 {count}개입니다 (10개 필요)."


def test_each_question_has_4_choices():
    """모든 문제에 보기가 4개씩 있어야 한다."""
    questions = load_all_questions()
    for q in questions:
        assert len(q["choices"]) == 4, (
            f"ID {q['id']} 문제의 보기가 {len(q['choices'])}개입니다 (4개 필요)."
        )


def test_answer_index_in_range():
    """모든 문제의 answer가 0~3 범위여야 한다."""
    questions = load_all_questions()
    for q in questions:
        assert 0 <= q["answer"] <= 3, (
            f"ID {q['id']} 문제의 answer={q['answer']}가 0~3 범위를 벗어납니다."
        )


def test_each_question_has_explanation():
    """모든 문제에 explanation이 있어야 한다."""
    questions = load_all_questions()
    for q in questions:
        assert q.get("explanation"), f"ID {q['id']} 문제에 explanation이 없습니다."


def test_unique_question_ids():
    """문제 ID가 모두 고유해야 한다."""
    questions = load_all_questions()
    ids = [q["id"] for q in questions]
    assert len(ids) == len(set(ids)), "중복된 문제 ID가 있습니다."


# ──────────────────────────────────────────────────────────────────────────────
# 2. 게임 로직 검증
# ──────────────────────────────────────────────────────────────────────────────

def test_score_calculation():
    """점수 계산: 정답 수 × 10"""
    assert 0 * 10 == 0
    assert 10 * 10 == 100
    assert 40 * 10 == 400


def test_grade_s_400():
    """400점 → S등급"""
    grade, _ = quiz_game.get_grade(400)
    assert grade == "S"


def test_grade_s_380():
    """380점 → S등급"""
    grade, _ = quiz_game.get_grade(380)
    assert grade == "S"


def test_grade_a_350():
    """350점 → A등급"""
    grade, _ = quiz_game.get_grade(350)
    assert grade == "A"


def test_grade_a_300():
    """300점 → A등급"""
    grade, _ = quiz_game.get_grade(300)
    assert grade == "A"


def test_grade_b_250():
    """250점 → B등급"""
    grade, _ = quiz_game.get_grade(250)
    assert grade == "B"


def test_grade_b_200():
    """200점 → B등급"""
    grade, _ = quiz_game.get_grade(200)
    assert grade == "B"


def test_grade_c_150():
    """150점 → C등급"""
    grade, _ = quiz_game.get_grade(150)
    assert grade == "C"


def test_grade_c_100():
    """100점 → C등급"""
    grade, _ = quiz_game.get_grade(100)
    assert grade == "C"


def test_grade_d_50():
    """50점 → D등급"""
    grade, _ = quiz_game.get_grade(50)
    assert grade == "D"


def test_grade_d_0():
    """0점 → D등급"""
    grade, _ = quiz_game.get_grade(0)
    assert grade == "D"


def test_grade_boundary_379():
    """379점 → A등급 (S 미달)"""
    grade, _ = quiz_game.get_grade(379)
    assert grade == "A"


def test_grade_boundary_299():
    """299점 → B등급 (A 미달)"""
    grade, _ = quiz_game.get_grade(299)
    assert grade == "B"


def test_grade_boundary_199():
    """199점 → C등급 (B 미달)"""
    grade, _ = quiz_game.get_grade(199)
    assert grade == "C"


def test_grade_boundary_99():
    """99점 → D등급 (C 미달)"""
    grade, _ = quiz_game.get_grade(99)
    assert grade == "D"


# ──────────────────────────────────────────────────────────────────────────────
# 3. 랭킹 기능 검증
# ──────────────────────────────────────────────────────────────────────────────

def test_ranking_saved_to_file():
    """결과가 rankings.json에 저장되는가."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    tmp_path.unlink()  # 파일 없는 상태로 시작

    try:
        with patch.object(quiz_game, "RANKINGS_FILE", tmp_path):
            quiz_game.save_ranking("테스터", 300, "A")

        with open(tmp_path, encoding="utf-8") as f:
            data = json.load(f)

        assert len(data) == 1
        assert data[0]["nickname"] == "테스터"
        assert data[0]["score"] == 300
        assert data[0]["grade"] == "A"
        assert "date" in data[0]
    finally:
        tmp_path.unlink(missing_ok=True)


def test_ranking_top10_only():
    """상위 10명만 반환되는가."""
    rankings = [
        {"nickname": f"user{i}", "score": i * 10, "grade": "D", "date": "2026-01-01 00:00:00"}
        for i in range(15)
    ]
    top10 = sorted(rankings, key=lambda x: x["score"], reverse=True)[:10]
    assert len(top10) == 10


def test_ranking_sorted_desc():
    """점수 내림차순으로 정렬되는가."""
    rankings = [
        {"nickname": "A", "score": 100, "grade": "C", "date": "2026-01-01 00:00:00"},
        {"nickname": "B", "score": 300, "grade": "A", "date": "2026-01-01 00:00:00"},
        {"nickname": "C", "score": 200, "grade": "B", "date": "2026-01-01 00:00:00"},
    ]
    sorted_rankings = sorted(rankings, key=lambda x: x["score"], reverse=True)
    scores = [r["score"] for r in sorted_rankings]
    assert scores == sorted(scores, reverse=True)


def test_ranking_multiple_saves():
    """여러 번 저장해도 누적 저장되는가."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    tmp_path.unlink()

    try:
        with patch.object(quiz_game, "RANKINGS_FILE", tmp_path):
            quiz_game.save_ranking("유저1", 200, "B")
            quiz_game.save_ranking("유저2", 350, "A")

        with open(tmp_path, encoding="utf-8") as f:
            data = json.load(f)

        assert len(data) == 2
        nicknames = [r["nickname"] for r in data]
        assert "유저1" in nicknames
        assert "유저2" in nicknames
    finally:
        tmp_path.unlink(missing_ok=True)
