from flask import Flask, request, render_template_string
from flask_socketio import SocketIO, emit
from minecraft.networking.connection import Connection
from minecraft.networking.packets import ChatMessagePacket
import threading

app = Flask(__name__)
socketio = SocketIO(app)
bot = None

# HTML UI tích hợp (dark UI)
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
  <title>Minecraft Bot UI</title>
  <style>
    body { background: #121212; color: #eee; font-family: monospace; padding: 20px; }
    .container { max-width: 600px; margin: auto; }
    input, button {
      background: #1e1e1e; color: white; border: 1px solid #444;
      padding: 8px; margin-top: 5px;
    }
    pre {
      background: #1e1e1e; padding: 10px; height: 300px;
      overflow-y: auto; margin-top: 10px;
    }
  </style>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.5/socket.io.min.js"></script>
</head>
<body>
  <div class="container">
    <h2>🤖 Minecraft Bot UI</h2>
    <button onclick="startBot()">▶️ Start Bot</button>
    <form onsubmit="sendChat(event)">
      <input id="msg" placeholder="Gửi tin nhắn...">
      <button>Send</button>
    </form>
    <pre id="log"></pre>
  </div>
  <script>
    const socket = io();
    socket.on("log", msg => {
      document.getElementById("log").textContent += msg + "\\n";
    });

    function startBot() {
      fetch("/start", { method: "POST" });
    }

    function sendChat(e) {
      e.preventDefault();
      const msg = document.getElementById("msg").value;
      fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: "message=" + encodeURIComponent(msg)
      });
      document.getElementById("msg").value = "";
    }
  </script>
</body>
</html>
"""

# Bot điều khiển pyCraft
class MinecraftBot:
    def __init__(self, host, port, username, log_callback):
        self.conn = Connection(host=host, port=port, username=username)
        self.conn.register_packet_listener(self.handle_chat, ChatMessagePacket)
        self.log_callback = log_callback

    def handle_chat(self, chat_packet):
        self.log_callback(f"[CHAT] {chat_packet.json_data}")

    def start(self):
        threading.Thread(target=self.conn.connect).start()
        self.log_callback("[INFO] Bot đang kết nối...")

    def send_chat(self, message):
        packet = ChatMessagePacket()
        packet.message = message
        self.conn.write_packet(packet)
        self.log_callback(f"[BOT] Gửi: {message}")

# Flask route
@app.route("/")
def index():
    return render_template_string(HTML_PAGE)

@app.route("/start", methods=["POST"])
def start_bot():
    global bot
    if bot is None:
        def log(msg): socketio.emit("log", msg)
        bot = MinecraftBot("localhost", 25565, "FlaskBot", log)
        bot.start()
        return "Bot started"
    return "Bot already running"

@app.route("/chat", methods=["POST"])
def chat():
    global bot
    msg = request.form.get("message", "")
    if bot:
        bot.send_chat(msg)
        return "Message sent"
    return "Bot not running", 400

if __name__ == "__main__":
    socketio.run(app, debug=True)
