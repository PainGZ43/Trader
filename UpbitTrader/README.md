# 🚀 Upbit Auto Trader

AI 기반 암호화폐 자동매매 프로그램

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Planning-yellow.svg)](docs/README_PLAN.md)

---

## 📖 프로젝트 소개

Upbit Auto Trader는 **인공지능(AI)**과 **기술적 지표**를 결합하여 암호화폐 시장에서 자동으로 매매를 수행하는 프로그램입니다.

### 주요 특징

- 🤖 **AI 기반 예측**: LSTM/GRU 딥러닝 모델을 활용한 가격 예측
- 📊 **실시간 모니터링**: WebSocket 기반 실시간 시세 및 차트
- 📈 **다양한 기술적 지표**: MA, RSI, MACD, 볼린저밴드 등 20+ 지표
- 🎯 **백테스팅**: 과거 데이터로 전략 검증 및 최적화
- 🛡️ **리스크 관리**: 자동 손절/익절, 포지션 관리
- 💻 **사용자 친화적 UI**: PyQt5 기반 직관적인 인터페이스
- 🔔 **알림 기능**: 카카오톡 알림 지원
- 🔄 **24/7 운영**: 안정적인 자동 재연결 및 에러 복구

---

## 🎥 스크린샷

> 💡 UI는 Phase 7에서 구현 예정입니다.

---

## 🏗️ 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                    사용자 인터페이스                      │
│              (PyQt5 기반 GUI)                            │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│                   트레이딩 엔진                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ 전략관리  │  │ 주문실행  │  │리스크관리│              │
│  └──────────┘  └──────────┘  └──────────┘              │
└────┬─────────────┬─────────────┬──────────────────────┘
     │             │             │
┌────┴────┐  ┌────┴────┐  ┌────┴────┐
│ AI 모델  │  │ Upbit   │  │ Database│
│ (예측)   │  │  API    │  │ (SQLite)│
└─────────┘  └─────────┘  └─────────┘
```

자세한 아키텍처는 [implementation_plan.md](docs/implementation_plan.md)를 참조하세요.

---

## 🚀 빠른 시작

### 1. 사전 요구사항

- Python 3.9 이상
- Upbit 계정 및 API 키
- 최소 8GB RAM (AI 모델 학습 시)

### 2. 설치

```bash
# 저장소 클론 (또는 다운로드)
cd e:\GitHub\UpbitTrader

# 가상 환경 생성 및 활성화
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 의존성 설치
pip install -r requirements.txt
```

### 3. 설정

```bash
# .env 파일 생성
copy .env.example .env

# 텍스트 에디터로 .env 파일 열어서 API 키 입력
# UPBIT_ACCESS_KEY=your_access_key_here
# UPBIT_SECRET_KEY=your_secret_key_here
```

### 4. 실행

```bash
# 프로그램 시작
python main.py
```

자세한 설치 가이드는 [docs/README_PLAN.md](docs/README_PLAN.md#-빠른-시작-가이드)를 참조하세요.

---

## 📚 문서

### 개발 계획서
- **[전체 개발 계획](docs/implementation_plan.md)** - 프로젝트 전체 개요
- **[빠른 참조 가이드](docs/README_PLAN.md)** - Phase별 요약 및 타임라인
- **[작업 체크리스트](docs/task.md)** - 현재 진행 상황

### Phase별 상세 계획
1. [Phase 1: 기본 인프라](docs/phase1_infrastructure.md)
2. [Phase 2: API 통합](docs/phase2_api_integration.md)
3. [Phase 3: 데이터 처리](docs/phase3_data_processing.md)
4. [Phase 4: AI 모델](docs/phase4_ai_model.md)
5. [Phase 5-9: 트레이딩/UI/알림](docs/phase5-9_integrated.md)

### 사용 가이드
> 💡 Phase 7 완료 후 작성 예정

---

## 🛠️ 기술 스택

### 백엔드
- **Python 3.9+** - 메인 언어
- **pyupbit** - Upbit API 래퍼
- **TensorFlow/Keras** - AI 모델
- **SQLite** - 데이터베이스
- **pandas/numpy** - 데이터 분석

### 프론트엔드
- **PyQt5** - GUI 프레임워크
- **matplotlib/mplfinance** - 차트 시각화
- **pyqtgraph** - 실시간 차트

### 기술적 지표
- **TA-Lib** - 기술적 분석 라이브러리

---

## 📊 개발 진행 상황

```
전체 진행률: 10%

✅ 계획 완료 (100%)
⏳ Phase 1 (0%) - 기본 인프라
⏳ Phase 2 (0%) - API 통합
⏳ Phase 3 (0%) - 데이터 처리
⏳ Phase 4 (0%) - AI 모델
⏳ Phase 5 (0%) - 트레이딩
⏳ Phase 6 (0%) - 백테스팅
⏳ Phase 7 (0%) - UI
⏳ Phase 8 (0%) - 알림
⏳ Phase 9 (0%) - 안정성
```

최신 진행 상황은 [task.md](docs/task.md)에서 확인하세요.

---

## 🎯 로드맵

### 2025년 11월 - 12월
- [x] 개발 계획 수립
- [ ] Phase 1-3 구현 (인프라, API, 데이터)
- [ ] Phase 4 구현 (AI 모델)

### 2026년 1월
- [ ] Phase 5-6 구현 (트레이딩, 백테스팅)
- [ ] Phase 7 구현 (UI)

### 2026년 2월
- [ ] Phase 8-9 구현 (알림, 안정성)
- [ ] 통합 테스트 및 배포

---

## ⚠️ 면책 조항

> [!CAUTION]
> **투자 경고**
> 
> 본 프로그램은 **교육 및 연구 목적**으로 제작되었습니다.
> 
> - 암호화폐 투자는 원금 손실의 위험이 있습니다
> - AI 예측이 항상 정확한 것은 아닙니다
> - 과거 성과가 미래 수익을 보장하지 않습니다
> - 투자 손실에 대한 책임은 사용자에게 있습니다
> - 충분한 테스트 없이 실전 사용을 금지합니다
> - 잃어도 괜찮은 금액만 투자하세요

---

## 🔒 보안

### API 키 관리
- `.env` 파일은 절대 Git에 커밋하지 마세요
- API 키는 **출금 권한을 제거**한 상태로 사용하세요
- 2단계 인증(2FA)를 활성화하세요

### 권장 사항
- 테스트 계정 사용 권장
- 소액부터 시작 (10만원 이하)
- 일일 손실 한도 설정

---

## 🤝 기여하기

> 💡 현재는 개인 프로젝트로 진행 중입니다.

---

## 📄 라이선스

MIT License - 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

---

## 📞 문의

- **GitHub Issues**: 버그 리포트 및 기능 제안
- **Email**: your-email@example.com

---

## 🙏 감사의 말

본 프로젝트는 다음 오픈소스 프로젝트들을 활용합니다:

- [pyupbit](https://github.com/sharebook-kr/pyupbit) - Upbit API 래퍼
- [TensorFlow](https://www.tensorflow.org/) - 딥러닝 프레임워크
- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) - GUI 프레임워크
- [TA-Lib](https://mrjbq7.github.io/ta-lib/) - 기술적 분석

---

## 📈 성과 목표

| 지표 | 목표 |
|------|------|
| 샤프 비율 | > 1.0 |
| 최대 낙폭 (MDD) | < 15% |
| 승률 | > 55% |
| 월 평균 수익률 | 5-10% |
| 시스템 가동률 | > 99% |

> ⚠️ 위 목표는 이상적인 시장 환경을 가정한 것이며, 실제 성과와 다를 수 있습니다.

---

**마지막 업데이트**: 2025-11-22  
**버전**: 1.0  
**상태**: 📋 계획 단계

---

<div align="center">

**⭐ 이 프로젝트가 도움이 되셨다면 Star를 눌러주세요! ⭐**

Made with ❤️ and Python

</div>
