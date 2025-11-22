# Upbit Auto Trader - 개발 문서

본 폴더는 Upbit 자동매매 프로그램 개발을 위한 모든 계획 문서를 포함합니다.

## 📚 문서 구조

### 📋 주요 문서

#### 1. [README_PLAN.md](README_PLAN.md)
**빠른 시작 가이드 및 전체 요약**
- Phase별 요약
- 개발 타임라인 (Gantt 차트)
- 빠른 시작 가이드
- 다음 액션 아이템

👉 **처음 보시는 분은 이 문서부터 읽으세요!**

#### 2. [implementation_plan.md](implementation_plan.md)
**전체 개발 계획서**
- 프로젝트 개요 및 목표
- 기술 스택
- 시스템 아키텍처
- 9개 Phase 개요
- 16주 개발 일정
- 위험 요소 및 대응 방안
- 검증 계획

#### 3. [task.md](task.md)
**작업 체크리스트**
- 현재 진행 상황 추적
- 단계별 완료 여부

---

### 🔧 Phase별 상세 계획

#### [phase1_infrastructure.md](phase1_infrastructure.md)
**Phase 1: 기본 인프라 구축 (3-5일)**
- 프로젝트 폴더 구조
- 의존성 패키지 관리
- 환경 설정 시스템
- 데이터베이스 스키마
- 기본 유틸리티

#### [phase2_api_integration.md](phase2_api_integration.md)
**Phase 2: Upbit API 통합 (4-6일)**
- REST API 래퍼
- WebSocket 실시간 데이터
- Rate Limiting 관리
- 에러 처리 및 재연결

#### [phase3_data_processing.md](phase3_data_processing.md)
**Phase 3: 데이터 수집 및 처리 (4-5일)**
- OHLCV 데이터 수집
- 기술적 지표 계산 (MA, RSI, MACD 등)
- 데이터 전처리
- 캐싱 시스템

#### [phase4_ai_model.md](phase4_ai_model.md)
**Phase 4: AI 모델 개발 (5-7일)**
- LSTM/GRU 모델 아키텍처
- 학습 데이터 생성
- 모델 학습 파이프라인
- 실시간 예측 서비스
- 모델 평가 및 재학습

#### [phase5-9_integrated.md](phase5-9_integrated.md)
**Phase 5-9: 통합 계획**
- **Phase 5**: 트레이딩 로직 (4-6일)
- **Phase 6**: 백테스팅 시스템 (4-5일)
- **Phase 7**: 사용자 인터페이스 (6-7일)
- **Phase 8**: 알림 및 모니터링 (2-3일)
- **Phase 9**: 시스템 안정성 (3-4일)

---

## 🗂️ 문서 읽는 순서

### 처음 시작하시는 분
1. **[README_PLAN.md](README_PLAN.md)** - 전체 개요 파악
2. **[implementation_plan.md](implementation_plan.md)** - 상세 계획 이해
3. **[phase1_infrastructure.md](phase1_infrastructure.md)** - 첫 번째 구현 시작

### 특정 Phase 구현 중
1. 해당 Phase 문서 정독
2. 체크리스트 확인
3. 구현 후 **[task.md](task.md)** 업데이트

### 전체 복습
- **[README_PLAN.md](README_PLAN.md)** - 진행 상황 점검
- **각 Phase 문서** - 세부 사항 재확인

---

## 📊 개발 진행 상황

```
전체 진행률: [██░░░░░░░░░░░░░░░░░░] 10%

✅ 계획 단계: 100% 완료
⏳ Phase 1: 0% (준비 중)
⏳ Phase 2: 0%
⏳ Phase 3: 0%
⏳ Phase 4: 0%
⏳ Phase 5-9: 0%
⏳ 테스트: 0%
⏳ 배포: 0%
```

---

## 🎯 다음 해야 할 일

### 즉시 수행
- [ ] Upbit API 키 발급
- [ ] 개발 환경 설정 (Python 3.9+, virtualenv)
- [ ] Phase 1 구현 시작

### 이번 주 목표
- [ ] Phase 1 완료
- [ ] Phase 2 시작 (API 연동)

---

## 📝 문서 업데이트 이력

| 날짜 | 버전 | 변경 내용 |
|------|------|-----------|
| 2025-11-22 | 1.0 | 초기 계획 문서 작성 완료 |
|  |  | - 전체 개발 계획서 |
|  |  | - Phase 1-9 상세 계획 |
|  |  | - 빠른 참조 가이드 |

---

## ⚠️ 중요 공지

> [!IMPORTANT]
> 본 문서들은 개발 과정에서 지속적으로 업데이트됩니다.
> - 새로운 요구사항 발견 시 반영
> - 구현 중 변경사항 기록
> - 문제 해결 방법 추가

> [!CAUTION]
> 실제 구현 시 다음 사항을 반드시 확인하세요:
> - API 키 보안 (절대 Git에 커밋 금지)
> - 소액 테스트부터 시작
> - 백테스팅 충분히 수행
> - 리스크 관리 설정

---

## 🔗 외부 참고 자료

### API 문서
- [Upbit API 공식 문서](https://docs.upbit.com/)
- [pyupbit 라이브러리](https://github.com/sharebook-kr/pyupbit)

### 기술 문서
- [TensorFlow 튜토리얼](https://www.tensorflow.org/tutorials)
- [PyQt5 문서](https://doc.qt.io/qtforpython/)
- [TA-Lib 문서](https://mrjbq7.github.io/ta-lib/)

### 트레이딩 전략
- 기술적 분석 이론
- 리스크 관리 전략
- 포트폴리오 이론

---

## 📞 문의 및 지원

- **Issues**: 버그 리포트 및 기능 제안
- **Discussions**: 질문 및 아이디어 공유
- **Wiki**: FAQ 및 팁 모음

---

**마지막 업데이트**: 2025-11-22
**문서 버전**: 1.0
**상태**: ✅ 계획 완료
