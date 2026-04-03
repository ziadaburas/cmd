const express = require('express');
const { exec } = require('child_process');

const app = express();
const port = process.env.PORT || 3000;

// للسماح باستقبال البيانات بصيغة JSON
app.use(express.json());

// عرض واجهة التيرمنال عند الدخول إلى الرابط الأساسي /
app.get('/', (req, res) => {
    const htmlContent = `
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Render Terminal</title>
        <style>
            body { background-color: #121212; color: #00ff00; font-family: 'Courier New', Courier, monospace; padding: 20px; font-size: 16px; margin: 0; height: 100vh; overflow-y: auto; }
            #output { white-space: pre-wrap; word-wrap: break-word; margin-bottom: 10px; }
            .error { color: #ff3333; }
            .command-line { color: #00bfff; margin-bottom: 5px; }
            #input-area { display: flex; align-items: center; }
            #prompt { color: #00ff00; margin-right: 10px; }
            #cmd { background: transparent; border: none; color: #00ff00; font-family: 'Courier New', Courier, monospace; font-size: 16px; flex-grow: 1; outline: none; }
        </style>
    </head>
    <body>
        <div id="output">مرحباً بك في تيرمنال Render. اكتب أمرك هنا...<br><br></div>
        <div id="input-area">
            <span id="prompt">render@server:~$</span>
            <input type="text" id="cmd" autofocus autocomplete="off">
        </div>

        <script>
            const cmdInput = document.getElementById('cmd');
            const outputDiv = document.getElementById('output');

            cmdInput.addEventListener('keypress', async function (e) {
                if (e.key === 'Enter') {
                    const command = cmdInput.value.trim();
                    if (!command) return;

                    // طباعة الأمر الذي تم إدخاله على الشاشة
                    outputDiv.innerHTML += '<div class="command-line">render@server:~$ ' + command + '</div>';
                    cmdInput.value = '';

                    try {
                        // إرسال الأمر للسيرفر
                        const response = await fetch('/run', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ cmd: command })
                        });
                        
                        const result = await response.text();
                        
                        // تنظيف النصوص وعرض الناتج
                        const safeResult = result.replace(/</g, "&lt;").replace(/>/g, "&gt;");
                        if(response.ok) {
                            outputDiv.innerHTML += '<div>' + safeResult + '<br></div>';
                        } else {
                            outputDiv.innerHTML += '<div class="error">' + safeResult + '<br></div>';
                        }
                    } catch (error) {
                        outputDiv.innerHTML += '<div class="error">Network Error: Could not reach the server.<br></div>';
                    }
                    
                    // النزول لأسفل الشاشة تلقائياً
                    window.scrollTo(0, document.body.scrollHeight);
                }
            });
        </script>
    </body>
    </html>
    `;
    res.send(htmlContent);
});

// المسار المسؤول عن استقبال الأمر من الواجهة وتنفيذه في نظام التشغيل
app.post('/run', (req, res) => {
    const command = req.body.cmd;

    if (!command) {
        return res.status(400).send("No command provided");
    }

    // تنفيذ الأمر في بيئة Render
    exec(command, (error, stdout, stderr) => {
        if (error) {
            // إذا كان هناك خطأ في تنفيذ الأمر (مثل أمر غير موجود أو لا توجد صلاحيات)
            return res.status(500).send(stderr || error.message);
        }
        // إرسال الناتج بنجاح
        res.send(stdout || "Command executed successfully (No output)");
    });
});

// تشغيل السيرفر
app.listen(port, () => {
    console.log(\`Terminal app listening on port \${port}\`);
});
