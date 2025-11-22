# 🚀 키움 REST API 빠른 시작 가이드

## 📌 시작하기 전에

### ✅ 체크리스트
- [ ] 키움증권 계좌 개설 완료
- [ ] 키움 API 서비스 신청 및 승인
- [ ] APP_KEY, SECRET_KEY 발급 완료
- [ ] Python 3.8~3.11 설치 확인

---

## 🎯 1단계: 환경 설정

### 방법 1: 자동 설정 (권장) ⭐

```bash
setup_env.bat
```

대화형 프롬프트에 따라 입력:
1. APP_KEY 입력
2. SECRET_KEY 입력
3. 계좌번호 입력 (8자리)
4. 모드 선택 (SIMULATION/REAL)

### 방법 2: 수동 설정

1. `.env.example`을 복사하여 `.env` 생성
2. `.env` 파일 편집:

```env
# Kiwoom REST API Credentials
APP_KEY=발급받은_앱키_여기_입력
SECRET_KEY=발급받은_시크릿키_여기_입력
ACCOUNT_NO=12345678

# System Settings
MODE=SIMULATION  # 처음에는 SIMULATION으로!
LOG_LEVEL=INFO
```

---

## 🧪 2단계: API 연결 테스트

### 전체 테스트 실행

```bash
python test_kiwoom.py all
```

또는 대화형 모드:

```bash
python test_kiwoom.py
```

### 개별 테스트

```bash
# 인증만 테스트
python test_kiwoom.py auth

# 시세 조회 테스트
python test_kiwoom.py price

# 계좌 조회 테스트
python test_kiwoom.py account
```

### 예상 결과

```
🚀 🚀 🚀 🚀 🚀 🚀 🚀 🚀 🚀 🚀 
키움 REST API 테스트 시작
🚀 🚀 🚀 🚀 🚀 🚀 🚀 🚀 🚀 🚀 

============================================================
1️⃣  인증 테스트
============================================================
✅ 인증 성공!
   Access Token: eyJhbGciOiJIUzI1NiIs...
   만료 시간: 2025-11-22 15:34:28

============================================================
2️⃣  현재가 조회 테스트
============================================================
📊 삼성전자 (005930) 조회 중...
✅ 조회 성공!
   종목명: 삼성전자
   현재가: 70,500원
   등락률: +2.14%
   거래량: 12,345,678주

...

결과: 4/4 테스트 통과
🎉 모든 테스트 통과! API 연동 준비 완료
```

---

## 🔧 3단계: 실제 코드에 적용

### 기존 kiwoom_api.py 교체

```bash
# 백업
copy kiwoom_api.py kiwoom_api_mock.py

# 실제 구현으로 교체
copy kiwoom_api_real.py kiwoom_api.py
```

또는 직접 수정:

```python
# main.py 또는 trading_manager.py에서

# 기존 (Mock)
from kiwoom_api import KiwoomAPI
api = KiwoomAPI()

# 새로운 (Real)
from kiwoom_api_real import KiwoomRESTAPI
api = KiwoomRESTAPI(is_virtual=True)  # 모의투자
# api = KiwoomRESTAPI(is_virtual=False)  # 실전
```

### 사용 예시

```python
import asyncio
from kiwoom_api_real import KiwoomRESTAPI

async def main():
    # API 초기화 (모의투자)
    api = KiwoomRESTAPI(is_virtual=True)
    
    try:
        # 시작
        await api.start()
        
        # 현재가 조회
        price = await api.get_current_price("005930")
        print(f"삼성전자: {price['price']:,}원")
        
        # 계좌 조회
        balance = await api.get_account_balance()
        print(f"총 자산: {balance['total_asset']:,}원")
        
        # 매수 주문 (주의!)
        # order = await api.send_buy_order("005930", 1, 70000)
        # print(f"주문 완료: {order}")
        
    finally:
        await api.close()

asyncio.run(main())
```

---

## ⚠️ 4단계: 안전 수칙

### 모의투자로 충분히 테스트

```python
# .env 파일
MODE=SIMULATION
```

```python
# 코드
api = KiwoomRESTAPI(is_virtual=True)  # 모의투자!
```

### 실전 전 확인사항

- [ ] 모의투자에서 최소 1주일 이상 테스트
- [ ] 수익률, MDD 등 성과 확인
- [ ] 손절/익절 로직 정상 작동 확인
- [ ] Rate Limit 안전하게 설정
- [ ] 로그 모니터링 시스템 확인

### 실전 배포

```python
# .env 파일
MODE=REAL
```

```python
# 코드
api = KiwoomRESTAPI(is_virtual=False)  # 실전
```

**처음에는 소액으로 시작하세요!**

---

## 🐛 문제 해결

### "Unauthorized" 오류

```
원인: 잘못된 APP_KEY/SECRET_KEY
해결: 
1. .env 파일 확인
2. 키움 개발자 포털에서 키 재확인
3. 공백, 줄바꿈 없는지 확인
```

### "Rate Limit Exceeded"

```
원인: API 호출 너무 빈번
해결:
1. kiwoom_api_real.py에서 rate_limit_delay 증가
   self.rate_limit_delay = 0.5  # 0.2 → 0.5
```

### "계좌번호 오류"

```
원인: 잘못된 ACCOUNT_NO
해결:
1. 영웅문(HTS)에서 계좌번호 확인
2. 앞 8자리만 입력 (대시 제외)
   예: 12345678
```

### WebSocket 연결 실패

```
원인: approval_key 누락 또는 잘못된 URL
해결:
1. 키움 API 문서에서 WebSocket URL 확인
2. _get_approval_key() 함수 구현
```

---

## 📚 추가 리소스

### 문서
- [KIWOOM_REST_API_GUIDE.md](KIWOOM_REST_API_GUIDE.md) - 상세 가이드
- [kiwoom_api_real.py](kiwoom_api_real.py) - 실제 구현 코드
- [test_kiwoom.py](test_kiwoom.py) - 테스트 스크립트

### 키움 공식
- 키움증권: https://www.kiwoom.com
- 개발자 포털: https://apiportal.kiwoom.com
- 고객센터: 1544-9000

### 커뮤니티
- 네이버 카페: "키움 Open API"
- GitHub 예제 검색

---

## 🎓 학습 경로

### 초급 (1-2주)
1. ✅ 환경 설정
2. ✅ API 인증 및 테스트
3. ✅ 시세 조회
4. ✅ 계좌 조회

### 중급 (2-4주)
5. 🔄 모의투자 주문
6. 🔄 실시간 시세 (WebSocket)
7. 🔄 전략 백테스트
8. 🔄 리스크 관리

### 고급 (1-2개월)
9. ⏳ 실전 배포
10. ⏳ 성과 모니터링
11. ⏳ 전략 최적화
12. ⏳ 포트폴리오 관리

---

## ✨ 완료!

축하합니다! 키움 REST API 연동 준비가 완료되었습니다.

### 다음 단계

1. **테스트 실행**: `python test_kiwoom.py all`
2. **문서 읽기**: `KIWOOM_REST_API_GUIDE.md`
3. **모의투자 시작**: MODE=SIMULATION
4. **성과 모니터링**: 최소 1주일
5. **실전 배포**: 소액으로 시작

### 도움이 필요하면

- 📖 문서 재확인
- 🔍 로그 파일 확인 (`system.log`)
- 📞 키움 고객센터 문의
- 💬 커뮤니티 질문

**행운을 빕니다! 🍀**

---

<sub>마지막 업데이트: 2025-11-21</sub>
