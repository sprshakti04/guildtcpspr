import sys
import os
import subprocess
import signal
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Global variable to store the running process
# NOTE: This works best with 1 worker (see Deployment Step below)
script_process = None

@app.route('/')
def index():
    # Check if script is currently running
    is_running = False
    if script_process and script_process.poll() is None:
        is_running = True
        
    return render_template('index.html', running=is_running)

@app.route('/start', methods=['POST'])
def start_script():
    global script_process
    
    # If already running, do nothing
    if script_process and script_process.poll() is None:
        return redirect(url_for('index'))

    try:
        root_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(root_dir, 'main.py')
        
        # Start the script in the background (Non-blocking)
        # We redirect output to a log file so we can read it later if needed
        log_file = open(os.path.join(root_dir, 'script.log'), 'w')
        
        script_process = subprocess.Popen(
            [sys.executable, script_path],
            cwd=root_dir,
            stdout=log_file,
            stderr=log_file,
            shell=False
        )
        
    except Exception as e:
        print(f"Error starting script: {e}")

    return redirect(url_for('index'))

@app.route('/stop', methods=['POST'])
def stop_script():
    global script_process
    
    if script_process and script_process.poll() is None:
        # Kill the process
        script_process.terminate()  # Tries to stop nicely
        try:
            script_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            script_process.kill()   # Force kill if it refuses
            
        script_process = None

    return redirect(url_for('index'))

@app.route('/logs')
def view_logs():
    # Helper to see what the script is doing
    root_dir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(root_dir, 'script.log')
    content = ""
    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            content = f.read()
    return f"<pre>{content}</pre>"

if __name__ == '__main__':
    app.run(debug=True)
