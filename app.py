import sys
import os
import subprocess
import signal
from flask import Flask, render_template, request, redirect, url_for, jsonify

app = Flask(__name__)

# Global variables
script_process = None
LOG_FILE = 'script.log'

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
        
        # 1. Open the log file in 'write' mode (clears old logs)
        # buffering=1 ensures lines are written immediately
        log_f = open(os.path.join(root_dir, LOG_FILE), 'w', buffering=1)
        
        # 2. Start the script in the background
        # '-u' forces python to use unbuffered binary stdout/stderr
        script_process = subprocess.Popen(
            [sys.executable, '-u', script_path],
            cwd=root_dir,
            stdout=log_f,       # Send output to file
            stderr=subprocess.STDOUT, # Send errors to same file
            shell=False
        )
        
    except Exception as e:
        print(f"Error starting script: {e}")

    return redirect(url_for('index'))

@app.route('/stop', methods=['POST'])
def stop_script():
    global script_process
    
    if script_process and script_process.poll() is None:
        script_process.terminate()
        try:
            script_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            script_process.kill()
        script_process = None

    return redirect(url_for('index'))

@app.route('/get_logs')
def get_logs():
    # Read the log file and return it to the browser
    root_dir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(root_dir, LOG_FILE)
    
    content = ""
    if os.path.exists(log_path):
        try:
            with open(log_path, 'r') as f:
                content = f.read()
        except Exception:
            content = "Error reading logs..."
            
    return jsonify({"logs": content})

if __name__ == '__main__':
    app.run(debug=True)
