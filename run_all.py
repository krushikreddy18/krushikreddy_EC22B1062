import subprocess
import sys
import os
import time

# Start data ingestor in background
subprocess.Popen([sys.executable, "data_ingestor.py"])

# Wait a moment for DB to start
time.sleep(2)

# Start Streamlit app
os.system("streamlit run app.py")
