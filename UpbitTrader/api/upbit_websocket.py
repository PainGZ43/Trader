"""
Upbit WebSocket API - 실시간 데이터 스트리밍
"""
import json
import uuid
import websocket
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from datetime import datetime
import time


class UpbitWebSocketClient(QThread):
    """Upbit WebSocket 클라이언트
    
    실시간 데이터 수신:
    - ticker: 현재가, 변동률 등
    - orderbook: 호가 정보
    - trade: 체결 내역
    """
    
    # 시그널 정의
    ticker_updated = pyqtSignal(dict)      # 티커 데이터
    orderbook_updated = pyqtSignal(dict)   # 호가 데이터  
    trade_updated = pyqtSignal(dict)       # 체결 데이터
    connected = pyqtSignal()               # 연결 성공
    disconnected = pyqtSignal()            # 연결 종료
    error_occurred = pyqtSignal(str)       # 에러 발생
    
    def __init__(self, codes, types=['ticker']):
        """
        Args:
            codes: 구독할 코인 리스트 (예: ["KRW-BTC", "KRW-ETH"])
            types: 구독 타입 리스트 (ticker, orderbook, trade)
        """
        super().__init__()
        self.codes = codes
        self.types = types
        self.ws = None
        self.running = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        
    def run(self):
        """스레드 실행"""
        self.running = True
        self.connect()
        
    def connect(self):
        """WebSocket 연결"""
        try:
            # WebSocket URL
            url = "wss://api.upbit.com/websocket/v1"
            
            # WebSocket 생성
            self.ws = websocket.WebSocketApp(
                url,
                on_open=self.on_open,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close
            )
            
            # 연결 시작 (blocking)
            self.ws.run_forever()
            
        except Exception as e:
            print(f"WebSocket 연결 에러: {e}")
            self.error_occurred.emit(str(e))
            self.schedule_reconnect()
    
    def on_open(self, ws):
        """연결 성공 시 호출"""
        print("✅ WebSocket 연결 성공")
        self.connected.emit()
        self.reconnect_attempts = 0
        
        # 구독 요청 전송
        self.subscribe(self.codes, self.types)
    
    def on_message(self, ws, message):
        """메시지 수신 시 호출"""
        try:
            # bytes를 string으로 변환
            if isinstance(message, bytes):
                message = message.decode('utf-8')
            
            # JSON 파싱
            data = json.loads(message)
            
            # 타입에 따라 적절한 시그널 발생
            msg_type = data.get('type')
            
            if msg_type == 'ticker':
                self.ticker_updated.emit(data)
            elif msg_type == 'orderbook':
                self.orderbook_updated.emit(data)
            elif msg_type == 'trade':
                self.trade_updated.emit(data)
                
        except Exception as e:
            print(f"메시지 처리 에러: {e}")
    
    def on_error(self, ws, error):
        """에러 발생 시 호출"""
        print(f"❌ WebSocket 에러: {error}")
        self.error_occurred.emit(str(error))
    
    def on_close(self, ws, close_status_code, close_msg):
        """연결 종료 시 호출"""
        print(f"WebSocket 연결 종료 (code: {close_status_code}, msg: {close_msg})")
        self.disconnected.emit()
        
        # 재연결 시도
        if self.running:
            self.schedule_reconnect()
    
    def subscribe(self, codes, types):
        """코인 구독
        
        Args:
            codes: 코인 리스트 (예: ["KRW-BTC", "KRW-ETH"])
            types: 타입 리스트 (ticker, orderbook, trade)
        """
        if not self.ws:
            return
        
        try:
            # Upbit WebSocket 구독 형식
            # 최대 5개 코드씩 나눠서 구독 (Upbit 제한)
            for i in range(0, len(codes), 5):
                chunk_codes = codes[i:i+5]
                
                subscribe_data = [
                    {"ticket": str(uuid.uuid4())[:8]},
                ]
                
                for msg_type in types:
                    subscribe_data.append({
                        "type": msg_type,
                        "codes": chunk_codes,
                        "isOnlyRealtime": True  # 실시간 데이터만 수신
                    })
                
                subscribe_data.append({"format": "DEFAULT"})
                
                # JSON 전송
                self.ws.send(json.dumps(subscribe_data))
                print(f"📡 구독 요청: {chunk_codes} ({types})")
                
        except Exception as e:
            print(f"구독 에러: {e}")
            self.error_occurred.emit(str(e))
    
    def unsubscribe(self):
        """구독 취소"""
        if self.ws:
            self.ws.close()
    
    def schedule_reconnect(self):
        """재연결 스케줄링"""
        if not self.running:
            return
        
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            print(f"❌ 최대 재연결 시도 초과 ({self.max_reconnect_attempts}회)")
            self.error_occurred.emit("최대 재연결 시도 초과")
            return
        
        self.reconnect_attempts += 1
        wait_time = min(2 ** self.reconnect_attempts, 30)  # 최대 30초
        
        print(f"🔄 {wait_time}초 후 재연결 시도... ({self.reconnect_attempts}/{self.max_reconnect_attempts})")
        time.sleep(wait_time)
        
        if self.running:
            self.connect()
    
    def stop(self):
        """스레드 중지"""
        print("🛑 WebSocket 클라이언트 중지")
        self.running = False
        if self.ws:
            self.ws.close()
        self.quit()
        self.wait()


class MarketWebSocketUpdater(QThread):
    """마켓 리스트 전용 WebSocket 업데이터"""
    
    market_data_updated = pyqtSignal(dict)  # 개별 코인 데이터
    
    def __init__(self, codes):
        super().__init__()
        self.codes = codes
        self.ws_client = None
        
    def run(self):
        """스레드 실행"""
        # WebSocket 클라이언트 생성
        self.ws_client = UpbitWebSocketClient(
            codes=self.codes,
            types=['ticker']
        )
        
        # 시그널 연결
        self.ws_client.ticker_updated.connect(self.on_ticker_updated)
        self.ws_client.connected.connect(lambda: print("📡 마켓 데이터 스트리밍 시작"))
        self.ws_client.error_occurred.connect(lambda msg: print(f"에러: {msg}"))
        
        # WebSocket 시작
        self.ws_client.start()
        
        # 이벤트 루프 유지
        self.exec_()
    
    def on_ticker_updated(self, data):
        """티커 데이터 수신 시"""
        try:
            # Upbit WebSocket ticker 데이터 변환
            market_info = {
                'ticker': data.get('code'),  # 예: KRW-BTC
                'current_price': data.get('trade_price'),  # 현재가
                'change_percent': data.get('signed_change_rate', 0) * 100,  # 변동률 (%)
                'high_24h': data.get('high_price'),
                'low_24h': data.get('low_price'),
                'volume_24h': data.get('acc_trade_volume_24h'),
                'timestamp': data.get('timestamp'),
            }
            
            self.market_data_updated.emit(market_info)
            
        except Exception as e:
            print(f"티커 데이터 변환 에러: {e}")
    
    def stop(self):
        """스레드 중지"""
        if self.ws_client:
            self.ws_client.stop()
        self.quit()
        self.wait()
