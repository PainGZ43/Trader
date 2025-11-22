@echo off
echo Fixing NumPy version for TensorFlow compatibility...
pip uninstall -y numpy
pip install "numpy<2.0.0"
echo.
echo Done! Please restart the application.
pause
