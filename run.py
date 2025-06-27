import os
# Set environment variables to avoid Qt issues
# For Raspberry Pi:
os.environ["OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS"] = "0"  # Disable hardware acceleration
os.environ["PYTHONUNBUFFERED"] = "1"  # Ensure print statements are output immediately

# Display detection
if "DISPLAY" in os.environ:
    print(f"Display detected: {os.environ['DISPLAY']}")
else:
    print("No display detected, running in headless mode")
    os.environ["OPENCV_HEADLESS"] = "1"

import tkinter as tk
from interface.ui import Ui
import uvicorn
import website.web as web
from threading import Thread
import sys
import cv2

def run_web():
    uvicorn.run(web.app, host="0.0.0.0", port=8000, log_level=None)

if __name__ == "__main__":
    # Print system information
    print(f"Python version: {sys.version}")
    print(f"OpenCV version: {cv2.__version__}" if 'cv2' in sys.modules else "OpenCV not imported yet")
    print(f"Tkinter version: {tk.TkVersion}")
    
    # Start web server
    t = Thread(target=run_web, daemon=True)
    t.start()
    
    # Create and run main application
    app = Ui()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()