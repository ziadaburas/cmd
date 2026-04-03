import os
import pty
import subprocess
import select
from flask import Flask, render_template_string
from flask_socketio import SocketIO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret-terminal'
# تفعيل الـ WebSockets
#socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')
socketio = SocketIO(app, cors_allowed_origins="*")
# واجهة التيرمنال الاحترافية باستخدام xterm.js
HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Interactive Python Terminal</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/xterm/css/xterm.css" />
    <script src="https://cdn.jsdelivr.net/npm/xterm/lib/xterm.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        body { background-color: #000; margin: 0; padding: 10px; height: 100vh; box-sizing: border-box; display: flex; flex-direction: column; }
        #terminal { flex-grow: 1; width: 100%; height: 100%; }
    </style>
</head>
<body>
    <div id="terminal"></div>
    <script>
        // إعداد واجهة التيرمنال
        var term = new Terminal({
            cursorBlink: true,
            theme: { background: '#121212', foreground: '#00ff00' },
            fontFamily: '"Courier New", Courier, monospace',
            fontSize: 16
        });
        term.open(document.getElementById('terminal'));

        // الاتصال بالسيرفر عبر WebSockets
        var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

        socket.on('connect', function() {
            term.write('\\r\\n*** Connected to Render Terminal ***\\r\\n\\n');
        });

        // استقبال المخرجات من السيرفر وطباعتها على الشاشة
        socket.on('output', function(data) {
            term.write(data.output);
        });

        // إرسال ما يكتبه المستخدم (حرفاً بحرف) إلى السيرفر
        term.onData(function(data) {
            socket.emit('input', {input: data});
        });
    </script>
</body>
</html>
"""

# متغيرات عالمية لحفظ حالة التيرمنال
fd = None
child_pid = None

def read_from_pty():
    """دالة تعمل في الخلفية لقراءة أي شيء يظهر في التيرمنال وإرساله للمتصفح"""
    global fd
    max_read_bytes = 1024 * 20
    while True:
        socketio.sleep(0.01)
        if fd:
            # التحقق مما إذا كان هناك بيانات جاهزة للقراءة
            r, _, _ = select.select([fd], [], [], 0.1)
            if r:
                try:
                    # قراءة البيانات وإرسالها للمتصفح
                    output = os.read(fd, max_read_bytes).decode('utf-8', errors='replace')
                    socketio.emit('output', {'output': output})
                except OSError:
                    pass

@app.route('/')
def index():
    return render_template_string(HTML)

@socketio.on('connect')
def handle_connect():
    global fd, child_pid
    # إذا لم يكن هناك تيرمنال شغال، قم بإنشاء واحد جديد
    if fd is None:
        child_pid, fd = pty.fork()
        if child_pid == 0:
            # نحن الآن داخل العملية الفرعية، سنقوم بتشغيل Bash
            os.environ['TERM'] = 'xterm-256color'
            subprocess.run(['/bin/bash'])
        else:
            # تشغيل الدالة التي تقرأ المخرجات في الخلفية
            socketio.start_background_task(target=read_from_pty)

@socketio.on('input')
def handle_input(data):
    """استقبال ما يكتبه المستخدم وإدخاله إلى التيرمنال الفعلي"""
    global fd
    if fd:
        os.write(fd, data['input'].encode('utf-8'))

if __name__ == '__main__':
    # تشغيل السيرفر
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)
