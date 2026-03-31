# /quiz-ci — 전체 CI 파이프라인 실행

테스트 + 검증을 한 번에 실행하는 풀 CI 파이프라인입니다.
questions.json 수정 후 또는 코드 변경 후 실행합니다.

## 실행 단계 (순서대로)

### Step 1: 코드 품질 확인
```
python -m py_compile quiz_game.py validator.py
```
문법 오류가 있으면 즉시 중단하고 오류 위치를 알립니다.

### Step 2: 할루시네이션 검증
```
python -X utf8 validator.py
```
- ❌ 오류가 있으면 CI 실패 — questions.json 수정 필요
- ⚠️  경고가 있으면 목록을 표시하고 계속 진행

### Step 3: 단위 테스트
```
python -m pytest tests/test_quiz.py -v
```
테스트 실패 시 원인을 분석하고 수정 방법을 제안합니다.

### Step 4: 종합 리포트
```
전체 결과 요약:
  ✅ 코드 컴파일: OK/FAIL
  ✅ 할루시네이션 검증: X개 통과 / Y개 경고 / Z개 오류
  ✅ 단위 테스트: X/Y 통과
  
최종 상태: PASS / FAIL
```

모든 단계가 통과하면 "배포 준비 완료"를 표시합니다.
실패 항목이 있으면 우선순위별 수정 가이드를 제공합니다.
