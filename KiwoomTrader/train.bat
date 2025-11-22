@echo off
chcp 65001 >nul
echo ================================
echo AI 모델 학습 시작
echo ================================
echo.
echo 종목: 삼성전자 (005930)
echo 기간: 1년
echo 간격: 1시간봉
echo.
echo 학습 시간: 약 10-15분 소요
echo.
pause

python train_ai.py 005930 1y 1h

echo.
echo ================================
echo 학습 완료!
echo ================================
pause
