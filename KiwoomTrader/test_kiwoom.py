"""
키움 REST API 테스트 스크립트

사용법:
1. .env 파일에 실제 APP_KEY, SECRET_KEY 설정
2. python test_kiwoom.py
"""

import asyncio
import sys
from kiwoom_api_real import KiwoomRESTAPI
from logger import logger


async def test_authentication():
    """인증 테스트"""
    print("\n" + "="*60)
    print("1️⃣  인증 테스트")
    print("="*60)
    
    api = KiwoomRESTAPI(is_virtual=True)
    
    try:
        success = await api.authenticate()
        if success:
            print("✅ 인증 성공!")
            print(f"   Access Token: {api.access_token[:20]}...")
            print(f"   만료 시간: {api.token_expires_at}")
            return True
        else:
            print("❌ 인증 실패!")
            return False
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False
    finally:
        await api.close()


async def test_current_price():
    """시세 조회 테스트"""
    print("\n" + "="*60)
    print("2️⃣  현재가 조회 테스트")
    print("="*60)
    
    api = KiwoomRESTAPI(is_virtual=True)
    
    try:
        await api.start()
        
        # 삼성전자
        print("\n📊 삼성전자 (005930) 조회 중...")
        price_data = await api.get_current_price("005930")
        
        print(f"✅ 조회 성공!")
        print(f"   종목명: {price_data['name']}")
        print(f"   현재가: {price_data['price']:,}원")
        print(f"   등락률: {price_data['change']:+.2f}%")
        print(f"   거래량: {price_data['volume']:,}주")
        
        return True
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False
    finally:
        await api.close()


async def test_account_balance():
    """계좌 잔고 조회 테스트"""
    print("\n" + "="*60)
    print("3️⃣  계좌 잔고 조회 테스트")
    print("="*60)
    
    api = KiwoomRESTAPI(is_virtual=True)
    
    try:
        await api.start()
        
        print("\n💰 계좌 정보 조회 중...")
        balance = await api.get_account_balance()
        
        print(f"✅ 조회 성공!")
        print(f"   계좌번호: {balance['account_no']}")
        print(f"   총 자산: {balance['total_asset']:,}원")
        print(f"   예수금: {balance['cash']:,}원")
        print(f"\n📈 보유 종목:")
        
        if balance['stocks']:
            for stock in balance['stocks']:
                print(f"   - {stock['name']} ({stock['code']})")
                print(f"     수량: {stock['qty']:,}주")
                print(f"     평균단가: {stock['avg_price']:,}원")
                print(f"     현재가: {stock['current_price']:,}원")
                print(f"     손익률: {stock['profit_pct']:+.2f}%")
                print()
        else:
            print("   (보유 종목 없음)")
        
        return True
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False
    finally:
        await api.close()


async def test_buy_order_dry_run():
    """매수 주문 시뮬레이션 (실제 주문 X)"""
    print("\n" + "="*60)
    print("4️⃣  매수 주문 테스트 (DRY RUN)")
    print("="*60)
    
    print("\n⚠️  주의: 실제 주문을 실행하지 않습니다")
    print("실제 주문을 원하시면 코드의 주석을 해제하세요\n")
    
    api = KiwoomRESTAPI(is_virtual=True)
    
    try:
        await api.start()
        
        print("📝 주문 정보:")
        print("   종목: 삼성전자 (005930)")
        print("   수량: 1주")
        print("   가격: 70,000원 (지정가)")
        
        # 실제 주문 (주석 제거 시 실행)
        # order = await api.send_buy_order("005930", 1, 70000)
        # print(f"\n✅ 주문 완료!")
        # print(f"   주문번호: {order['order_no']}")
        # print(f"   상태: {order['status']}")
        
        print("\n⏸️  주문은 실행되지 않았습니다 (DRY RUN)")
        return True
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False
    finally:
        await api.close()


async def test_all():
    """모든 테스트 실행"""
    print("\n" + "🚀 "*20)
    print("키움 REST API 테스트 시작")
    print("🚀 "*20)
    
    results = []
    
    # 1. 인증
    results.append(await test_authentication())
    await asyncio.sleep(1)
    
    # 2. 시세 조회
    results.append(await test_current_price())
    await asyncio.sleep(1)
    
    # 3. 계좌 조회
    results.append(await test_account_balance())
    await asyncio.sleep(1)
    
    # 4. 주문 (Dry Run)
    results.append(await test_buy_order_dry_run())
    
    # 결과 요약
    print("\n" + "="*60)
    print("📊 테스트 결과 요약")
    print("="*60)
    
    tests = [
        "인증",
        "현재가 조회",
        "계좌 조회",
        "주문 (Dry Run)"
    ]
    
    for i, (test_name, result) in enumerate(zip(tests, results), 1):
        status = "✅ 성공" if result else "❌ 실패"
        print(f"{i}. {test_name}: {status}")
    
    success_count = sum(results)
    total_count = len(results)
    
    print(f"\n결과: {success_count}/{total_count} 테스트 통과")
    
    if success_count == total_count:
        print("\n🎉 모든 테스트 통과! API 연동 준비 완료")
    else:
        print("\n⚠️  일부 테스트 실패. 설정을 확인하세요")
        print("   - .env 파일의 APP_KEY, SECRET_KEY 확인")
        print("   - 키움 API 서비스 신청 및 승인 확인")
        print("   - 계좌번호 확인")


async def interactive_test():
    """대화형 테스트"""
    print("\n" + "="*60)
    print("🎮 대화형 테스트 모드")
    print("="*60)
    
    print("\n어떤 테스트를 실행하시겠습니까?")
    print("[1] 인증 테스트")
    print("[2] 현재가 조회")
    print("[3] 계좌 조회")
    print("[4] 주문 (Dry Run)")
    print("[5] 모든 테스트")
    print("[0] 종료")
    
    choice = input("\n선택 (0-5): ").strip()
    
    if choice == "1":
        await test_authentication()
    elif choice == "2":
        await test_current_price()
    elif choice == "3":
        await test_account_balance()
    elif choice == "4":
        await test_buy_order_dry_run()
    elif choice == "5":
        await test_all()
    elif choice == "0":
        print("👋 테스트 종료")
        return
    else:
        print("❌ 잘못된 선택입니다")


if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════════════════════════╗
    ║         키움 REST API 테스트 스크립트                  ║
    ║                                                        ║
    ║  ⚠️  주의사항:                                         ║
    ║  1. 모의투자 계좌로 테스트합니다                       ║
    ║  2. .env 파일에 실제 키 설정이 필요합니다              ║
    ║  3. 실제 주문은 실행되지 않습니다 (Dry Run)            ║
    ╚════════════════════════════════════════════════════════╝
    """)
    
    # 명령줄 인자 확인
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "auth":
            asyncio.run(test_authentication())
        elif arg == "price":
            asyncio.run(test_current_price())
        elif arg == "account":
            asyncio.run(test_account_balance())
        elif arg == "order":
            asyncio.run(test_buy_order_dry_run())
        elif arg == "all":
            asyncio.run(test_all())
        else:
            print(f"❌ 알 수 없는 인자: {arg}")
            print("사용법: python test_kiwoom.py [auth|price|account|order|all]")
    else:
        # 대화형 모드
        asyncio.run(interactive_test())
