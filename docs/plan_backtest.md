# 백테스팅 구현 계획

## 목표 설명
실제 과거 데이터(2020년~현재)를 사용하여 증분 업데이트와 효율적인 일괄 처리를 지원하는 강력한 백테스팅 환경을 구축합니다.

## 사용자 검토 필요 사항
> [!NOTE]
> 2000개 이상의 종목에 대한 4년치 데이터를 처음 다운로드할 때는 상당한 시간(수 시간)이 소요될 수 있습니다. 이후 업데이트는 빠르게 진행됩니다.

## 변경 제안

### 데이터 관리
#### [NEW] [scripts/manage_data.py](file:///e:/GitHub/Trader/PainTrader/scripts/manage_data.py)
- 과거 데이터를 관리하기 위한 통합 스크립트를 생성합니다.
- **기능**:
    - `download`: 2020년부터의 모든 종목(필터링 적용) 초기 다운로드.
    - `update`: `stock.get_market_ohlcv(date, market="ALL")`을 사용하여 누락된 날짜의 데이터를 빠르게 증분 업데이트.
    - `filter`: 스팩(SPAC), ETF, 우선주, 동전주 등을 일관되게 필터링.
    - `validate`: 데이터 무결성 검사.

### 백테스팅
#### [MODIFY] [scripts/run_backtest_with_csv.py](file:///e:/GitHub/Trader/PainTrader/scripts/run_backtest_with_csv.py)
- `manage_data.py`와 통합 (또는 생성된 데이터 파일 사용).
- 리포팅 개선 (상세 매매 로그 저장).
- 슬리피지 및 수수료 설정을 위한 명령줄 인수 추가.

### 추가 고려사항 (Advanced Considerations)
#### 1. 생존 편향 (Survivorship Bias) 방지
- **문제**: 현재 상장된 종목만으로 백테스트하면, 과거에 상장폐지된 종목(주로 실적 저조)이 제외되어 수익률이 과대포장될 수 있습니다.
- **해결**: 2020년부터 매년 1월 1일 기준 종목 리스트를 모두 수집하여 합집합(Union)을 만듭니다. 상장폐지된 종목의 데이터도 확보하여 백테스트에 포함합니다.

#### 2. 수정주가 (Adjusted Price)
- `pykrx`는 기본적으로 수정주가를 제공합니다. 액면분할/병합이 반영된 가격을 사용하여 백테스트의 정확도를 높입니다.

#### 3. 데이터 저장 형식
- CSV는 호환성이 좋지만 속도가 느릴 수 있습니다. 데이터 크기가 커지면 `Parquet` 형식 도입을 고려합니다. (현재 일봉 데이터 수준에서는 CSV도 충분함)

## 검증 계획

### 자동화 테스트
- **테스트 1**: 데이터 다운로드 및 업데이트
    - `python scripts/manage_data.py --mode update` 실행 (최신 상태라면 빨라야 함).
    - CSV 파일 무결성 확인.
- **테스트 2**: 백테스트 실행
    - `python scripts/run_backtest_with_csv.py --limit 10` 실행 (소량 배치 테스트).
    - 결과 CSV 및 플롯 생성 확인.

### 수동 검증
- 생성된 자산 곡선(Equity Curve) 플롯 확인.
- 결과를 알려진 시장 움직임(예: 2020년 코로나 폭락, 2021년 상승장)과 비교.
