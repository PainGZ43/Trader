# 📘 키움 REST API 연동 가이드

## 🎯 목차
1. [키움 REST API 개요](#1-키움-rest-api-개요)
2. [앱키 발급 방법](#2-앱키-발급-방법)
3. [API 인증 프로세스](#3-api-인증-프로세스)
4. [주요 API 엔드포인트](#4-주요-api-엔드포인트)
5. [실전 연동 가이드](#5-실전-연동-가이드)
6. [테스트 방법](#6-테스트-방법)
7. [문제 해결](#7-문제-해결)

---

## 1. 키움 REST API 개요

### 📌 키움 REST API란?
키움증권에서 제공하는 HTTP 기반 주식 거래 API입니다.

### 📖 공식 문서
- **공식 사이트**: https://www.kiwoom.com
- **개발자 센터**: https://apiportal.kiwoom.com (또는 https://openapi.kiwoom.com)
- **API 문서**: 로그인 후 다운로드 가능

### 🔑 주요 특징
- OAuth 2.0 인증
- REST/WebSocket 지원
- 실시간 시세 제공
- 주문 체결 가능
- Rate Limit: 초당 약 5-10회 (정확한 수치는 문서 확인)

---

## 2. 앱키 발급 방법

### 📋 발급 절차

1. **키움증권 계좌 개설**
   - https://www.kiwoom.com 에서 계좌 개설
   - HTS(영웅문) 설치 및 로그인 확인

2. **API 서비스 신청**
   - 키움증권 홈페이지 로그인
   - 고객센터 → API 서비스 신청
   - 또는 영업점 방문 신청

3. **앱키 발급**
   - 개발자 포털 접속: https://apiportal.kiwoom.com
   - 로그인 후 "앱 등록" 메뉴
   - 앱 이름 입력 (예: "Premium AI Trader")
   - 앱키(App Key), 시크릿키(Secret Key) 발급

4. **승인 대기**
   - 일반적으로 1-3 영업일 소요
   - 승인 완료 시 이메일/SMS 통보

### 📝 필요한 정보
```
APP_KEY=발급받은_앱키_입력
SECRET_KEY=발급받은_시크릿키_입력
ACCOUNT_NO=계좌번호_8자리
```

---

## 3. API 인증 프로세스

### 🔐 OAuth 2.0 인증 흐름

```
1. 토큰 발급 요청
   POST /oauth/token
   {
     "grant_type": "password",
     "appkey": "YOUR_APP_KEY",
     "appsecret": "YOUR_SECRET_KEY"
   }

2. Access Token 받기
   Response: {
     "access_token": "eyJhbGci...",
     "token_type": "Bearer",
     "expires_in": 86400
   }

3. API 요청 시 헤더에 포함
   Authorization: Bearer eyJhbGci...
```

### ⏰ 토큰 갱신
- Access Token 유효기간: 24시간 (추정)
- 만료 시 재발급 필요
- Refresh Token 지원 여부는 문서 확인

---

## 4. 주요 API 엔드포인트

### 📊 시세 조회
```http
# 현재가 조회
GET /uapi/domestic-stock/v1/quotations/inquire-price
Headers: 
  - Authorization: Bearer {token}
  - appkey: {APP_KEY}
  - appsecret: {SECRET_KEY}
Query:
  - fid_cond_mrkt_div_code: J (주식)
  - fid_input_iscd: 005930 (종목코드)
```

### 📈 계좌 조회
```http
# 잔고 조회
GET /uapi/domestic-stock/v1/trading/inquire-balance
Headers:
  - Authorization: Bearer {token}
  - appkey: {APP_KEY}
  - appsecret: {SECRET_KEY}
  - tr_id: TTTC8434R (실전) / VTTC8434R (모의)
Query:
  - CANO: 계좌번호 앞 8자리
  - ACNT_PRDT_CD: 계좌상품코드 (보통 01)
```

### 💰 주문 실행
```http
# 매수 주문
POST /uapi/domestic-stock/v1/trading/order-cash
Headers:
  - Authorization: Bearer {token}
  - appkey: {APP_KEY}
  - appsecret: {SECRET_KEY}
  - tr_id: TTTC0802U (실전매수) / VTTC0802U (모의매수)
Body:
{
  "CANO": "12345678",
  "ACNT_PRDT_CD": "01",
  "PDNO": "005930",
  "ORD_DVSN": "00", // 지정가
  "ORD_QTY": "10",
  "ORD_UNPR": "70000"
}
```

### 🔴 실시간 시세 (WebSocket)
```javascript
ws://ops.kiwoom.com/websocket
// 접속 후 구독 메시지 전송
{
  "header": {
    "approval_key": "YOUR_APPROVAL_KEY",
    "tr_type": "1", // 등록
    "content-type": "utf-8"
  },
  "body": {
    "tr_id": "H0STCNT0", // 실시간 체결가
    "tr_key": "005930"
  }
}
```

---

## 5. 실전 연동 가이드

### Step 1: .env 파일 설정

```bash
# .env.example을 복사하여 .env 생성
cp .env.example .env
```

`.env` 파일 편집:
```env
# Kiwoom REST API Credentials
APP_KEY=발급받은_실제_앱키
SECRET_KEY=발급받은_실제_시크릿키
ACCOUNT_NO=12345678

# System Settings
MODE=REAL  # SIMULATION → REAL로 변경
LOG_LEVEL=INFO
```

### Step 2: 키움 API 문서 확인

1. 키움 개발자 포털에서 최신 API 문서 다운로드
2. 엔드포인트 URL 확인:
   - 실전: `https://openapi.kiwoom.com`
   - 모의: `https://openapivts.kiwoom.com`

### Step 3: kiwoom_api.py 업데이트

현재 `kiwoom_api.py`에는 Mock 구현만 되어 있습니다.
아래 섹션에서 실제 구현 코드를 제공합니다.

---

## 6. 테스트 방법

### 🧪 테스트 순서

1. **인증 테스트**
   ```python
   python test_kiwoom_auth.py
   ```

2. **시세 조회 테스트**
   ```python
   python test_kiwoom_price.py
   ```

3. **계좌 조회 테스트**
   ```python
   python test_kiwoom_account.py
   ```

4. **모의투자 주문 테스트**
   - MODE=SIMULATION으로 먼저 테스트
   - 모의투자 계좌번호 사용

5. **실전 주문 (매우 주의!)**
   - 소액으로 먼저 테스트
   - 로그 확인 필수

---

## 7. 문제 해결

### ❌ 자주 발생하는 오류

#### 1. "Unauthorized" (401)
- **원인**: 잘못된 APP_KEY/SECRET_KEY 또는 만료된 토큰
- **해결**: .env 파일 확인, 토큰 재발급

#### 2. "Rate Limit Exceeded" (429)
- **원인**: API 호출 횟수 초과
- **해결**: 요청 간 딜레이 증가 (현재 0.2초)

#### 3. "Invalid Account" (400)
- **원인**: 잘못된 계좌번호 또는 상품코드
- **해결**: CANO, ACNT_PRDT_CD 확인

#### 4. "WebSocket Connection Failed"
- **원인**: approval_key 누락 또는 잘못된 URL
- **해결**: WebSocket URL 및 인증키 확인

### 🆘 지원

- **키움증권 고객센터**: 1544-9000
- **API 기술지원**: api@kiwoom.com (추정)
- **개발자 커뮤니티**: 키움 개발자 포털 Q&A

---

## 📚 참고 자료

### 공식 문서
- 키움증권 OpenAPI 가이드 (PDF)
- REST API Reference
- WebSocket API Reference

### 커뮤니티
- 네이버 카페: "키움 Open API"
- GitHub: 키움 API 예제 코드

### 법적 고지
⚠️ **주의사항**
- 실제 거래는 본인 책임하에 수행하세요
- 자동매매 프로그램 사용 시 손실 가능
- 키움증권 이용약관 준수 필수

---

## ✅ 체크리스트

실전 배포 전 확인사항:

- [ ] 키움증권 계좌 개설 완료
- [ ] API 서비스 신청 및 승인
- [ ] APP_KEY, SECRET_KEY 발급
- [ ] .env 파일 설정 완료
- [ ] 모의투자 계좌로 충분한 테스트
- [ ] 리스크 관리 파라미터 설정
- [ ] 손실 제한 설정
- [ ] 로그 모니터링 시스템 구축
- [ ] 긴급 중지 버튼 테스트

---

**🚀 준비가 되었다면 다음 단계로 진행하세요!**
