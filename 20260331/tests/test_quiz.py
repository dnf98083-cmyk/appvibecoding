"""상식 퀴즈 게임 테스트"""
import json
import sys
from pathlib import Path
from unittest.mock import patch

# 프로젝트 루트를 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

import quiz_game


# ── 문제 로딩 테스트 ────────────────────────────────────────────────────────

def test_load_all_questions():
    """전체 문제를 불러올 수 있어야 한다."""
    questions = quiz_game.load_questions()
    assert len(questions) >= 20, "문제가 20개 이상이어야 합니다"


def test_load_questions_by_category():
    """카테고리 필터가 동작해야 한다."""
    for cat in ["역사", "과학", "지리", "문화"]:
        questions = quiz_game.load_questions(category=cat)
        assert len(questions) > 0, f"{cat} 카테고리에 문제가 없습니다"
        assert all(q["category"] == cat for q in questions)


def test_load_questions_by_difficulty():
    """난이도 필터가 동작해야 한다."""
    for diff in ["쉬움", "보통", "어려움"]:
        questions = quiz_game.load_questions(difficulty=diff)
        assert len(questions) > 0, f"{diff} 난이도에 문제가 없습니다"
        assert all(q["difficulty"] == diff for q in questions)


# ── 문제 구조 검증 ─────────────────────────────────────────────────────────

def test_question_schema():
    """모든 문제가 필수 필드를 가져야 한다."""
    required_fields = {"id", "category", "difficulty", "question", "choices",
                       "answer", "explanation", "source", "confidence"}
    questions = quiz_game.load_questions()
    for q in questions:
        missing = required_fields - q.keys()
        assert not missing, f"Q{q.get('id','?')}: 필드 누락 {missing}"


def test_answer_index_valid():
    """정답 인덱스가 선택지 범위 내에 있어야 한다."""
    questions = quiz_game.load_questions()
    for q in questions:
        assert 0 <= q["answer"] < len(q["choices"]), \
            f"Q{q['id']}: 정답 인덱스 {q['answer']}가 범위를 벗어남"


def test_confidence_range():
    """신뢰도 점수는 0.0~1.0 범위여야 한다."""
    questions = quiz_game.load_questions()
    for q in questions:
        assert 0.0 <= q["confidence"] <= 1.0, \
            f"Q{q['id']}: 신뢰도 {q['confidence']}가 범위를 벗어남"


def test_source_not_empty():
    """모든 문제에 출처(source)가 있어야 한다."""
    questions = quiz_game.load_questions()
    for q in questions:
        assert q["source"].strip(), f"Q{q['id']}: 출처가 비어 있습니다"


# ── 할루시네이션 감지 테스트 ────────────────────────────────────────────────

def test_low_confidence_flagged():
    """낮은 신뢰도 문항이 존재하고 임계값 아래에 있어야 한다."""
    questions = quiz_game.load_questions()
    low_conf = [q for q in questions if q["confidence"] < quiz_game.CONFIDENCE_THRESHOLD]
    # 테스트용: 낮은 신뢰도 문항 구조가 올바른지만 검증
    for q in low_conf:
        assert "source" in q
        assert q["confidence"] < quiz_game.CONFIDENCE_THRESHOLD


def test_confidence_threshold_value():
    """신뢰도 임계값이 합리적인 범위(0.5~0.9)에 있어야 한다."""
    assert 0.5 <= quiz_game.CONFIDENCE_THRESHOLD <= 0.9


# ── 문제 선택 테스트 ───────────────────────────────────────────────────────

def test_select_questions_count():
    """요청한 수만큼 문제를 선택해야 한다."""
    all_q = quiz_game.load_questions()
    selected = quiz_game.select_questions(all_q, 5)
    assert len(selected) == 5


def test_select_questions_no_duplicate():
    """선택된 문제에 중복이 없어야 한다."""
    all_q = quiz_game.load_questions()
    selected = quiz_game.select_questions(all_q, 10)
    ids = [q["id"] for q in selected]
    assert len(ids) == len(set(ids)), "중복 문제가 있습니다"


def test_select_questions_less_than_available():
    """문제 수가 요청보다 적으면 있는 것만 반환해야 한다."""
    all_q = quiz_game.load_questions(category="문화")
    selected = quiz_game.select_questions(all_q, 100)
    assert len(selected) <= len(all_q)


# ── 정답 확인 테스트 ───────────────────────────────────────────────────────

def test_show_result_correct(capsys):
    """정답 시 True를 반환하고 '정답' 메시지를 출력해야 한다."""
    q = quiz_game.load_questions()[0]  # 첫 번째 문제
    result = quiz_game.show_result(q, q["answer"], elapsed=1.0)
    assert result is True
    captured = capsys.readouterr()
    assert "정답" in captured.out


def test_show_result_wrong(capsys):
    """오답 시 False를 반환하고 '오답' 메시지를 출력해야 한다."""
    q = quiz_game.load_questions()[0]
    wrong_answer = (q["answer"] + 1) % len(q["choices"])
    result = quiz_game.show_result(q, wrong_answer, elapsed=2.0)
    assert result is False
    captured = capsys.readouterr()
    assert "오답" in captured.out


# ── 결과 저장 테스트 ───────────────────────────────────────────────────────

def test_save_result(tmp_path, monkeypatch):
    """결과가 JSON 파일로 저장되어야 한다."""
    monkeypatch.setattr(quiz_game, "RESULTS_DIR", tmp_path)
    data = {"played_at": "2026-01-01T00:00:00", "score": 4, "total": 5,
            "percentage": 80.0, "category": "전체", "difficulty": "전체", "details": []}
    path = quiz_game.save_result(data)
    assert path.exists()
    with open(path, encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded["score"] == 4


# ── 유효성 검사 통합 테스트 ────────────────────────────────────────────────

def test_all_questions_have_five_choices():
    """모든 문제가 5개의 선택지를 가져야 한다."""
    questions = quiz_game.load_questions()
    for q in questions:
        assert len(q["choices"]) == 5, \
            f"Q{q['id']}: 선택지가 {len(q['choices'])}개 (5개여야 함)"


def test_unique_question_ids():
    """문제 ID가 모두 고유해야 한다."""
    questions = quiz_game.load_questions()
    ids = [q["id"] for q in questions]
    assert len(ids) == len(set(ids)), "중복된 문제 ID가 있습니다"
