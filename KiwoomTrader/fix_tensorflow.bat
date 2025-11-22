@echo off
echo ========================================
echo TensorFlow Fix Script
echo Downgrading to TensorFlow 2.10.0
echo ========================================
echo.

echo Step 1: Uninstalling current TensorFlow...
pip uninstall -y tensorflow tensorflow-intel tensorflow-io-gcs-filesystem
echo.

echo Step 2: Installing compatible TensorFlow 2.10.0...
pip install tensorflow==2.10.0 protobuf==3.19.6
echo.

echo Step 3: Verifying installation...
python -c "import tensorflow as tf; print('TensorFlow version:', tf.__version__); print('GPU Available:', len(tf.config.list_physical_devices('GPU')) > 0)"
echo.

echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo If you see a version number above, TensorFlow is working correctly.
echo Press any key to exit...
pause >nul
