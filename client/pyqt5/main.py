import sys
import asyncio
import json # <-- 1. تم استيراد مكتبة JSON
import websockets
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QGroupBox
)
from PyQt5.QtCore import QThread, pyqtSignal, QObject

# ------------------ Worker Thread for asyncio ------------------
# (No changes needed in this class)
class AsyncWorker(QObject):
    received_message = pyqtSignal(str)
    connected = pyqtSignal()
    disconnected = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.websocket = None
        self.loop = asyncio.new_event_loop()

    def start_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def stop_loop(self):
        self.loop.call_soon_threadsafe(self.loop.stop)

    def connect(self, url, headers):
        asyncio.run_coroutine_threadsafe(self._connect(url, headers), self.loop)

    async def _connect(self, url, headers):
        try:
            self.websocket = await websockets.connect(url, additional_headers=headers)
            self.connected.emit()
            await self.receive_messages()
        except Exception as e:
            self.disconnected.emit(str(e))
    
    async def receive_messages(self):
        try:
            while True:
                msg = await self.websocket.recv()
                self.received_message.emit(msg)
        except websockets.ConnectionClosed as e:
            self.disconnected.emit(f"Connection closed: {e}")

    def send(self, message):
        if self.websocket:
            asyncio.run_coroutine_threadsafe(self.websocket.send(message), self.loop)

    def disconnect(self):
        if self.websocket:
            asyncio.run_coroutine_threadsafe(self.websocket.close(), self.loop)

# ------------------ Main GUI ------------------
class WebSocketClientGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WebSocket PyQt5 Client")
        self.worker = AsyncWorker()

        self.init_ui()
        self.setup_worker()
        
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.start_loop)
        self.thread.start()

    def init_ui(self):
        layout = QVBoxLayout()

        # Connection URL group
        url_group = QGroupBox("Connection URL")
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("URL:"))
        self.url_input = QLineEdit("ws://127.0.0.1:8000/ws/brocker/")
        url_layout.addWidget(self.url_input)
        url_group.setLayout(url_layout)
        layout.addWidget(url_group)

        # Headers group
        headers_group = QGroupBox("Headers")
        h_layout = QVBoxLayout()
        token_layout = QHBoxLayout()
        token_layout.addWidget(QLabel("Token:"))
        self.token_input = QLineEdit()
        token_layout.addWidget(self.token_input)
        h_layout.addLayout(token_layout)

        tag_layout = QHBoxLayout()
        tag_layout.addWidget(QLabel("Tags (comma-separated):"))
        self.tag_input = QLineEdit() # This is for headers
        tag_layout.addWidget(self.tag_input)
        h_layout.addLayout(tag_layout)

        btn_layout = QHBoxLayout()
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.connect_to_server)
        btn_layout.addWidget(self.connect_btn)
        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.setEnabled(False)
        self.disconnect_btn.clicked.connect(self.disconnect_from_server)
        btn_layout.addWidget(self.disconnect_btn)
        h_layout.addLayout(btn_layout)

        headers_group.setLayout(h_layout)
        layout.addWidget(headers_group)

        # --- MODIFICATION START ---
        # 2. Re-designed the Message group to have two fields
        msg_group = QGroupBox("Message")
        m_layout = QVBoxLayout() # Changed to QVBoxLayout for vertical alignment

        # Message input row
        message_row_layout = QHBoxLayout()
        message_row_layout.addWidget(QLabel("Message:"))
        self.msg_input = QLineEdit()
        message_row_layout.addWidget(self.msg_input)
        m_layout.addLayout(message_row_layout)
        
        # Tag input row (for the message payload)
        tag_row_layout = QHBoxLayout()
        tag_row_layout.addWidget(QLabel("Tag:"))
        self.tag_input_msg = QLineEdit() # Gave it a unique name
        tag_row_layout.addWidget(self.tag_input_msg)
        m_layout.addLayout(tag_row_layout)
        
        self.send_btn = QPushButton("Send as JSON")
        self.send_btn.setEnabled(False)
        self.send_btn.clicked.connect(self.send_message)
        m_layout.addWidget(self.send_btn) # Add the button at the bottom
        
        msg_group.setLayout(m_layout)
        layout.addWidget(msg_group)
        # --- MODIFICATION END ---

        # Received Messages
        self.received_text = QTextEdit()
        self.received_text.setReadOnly(True)
        layout.addWidget(self.received_text)

        self.clear_btn = QPushButton("Clear Messages")
        self.clear_btn.clicked.connect(self.received_text.clear)
        layout.addWidget(self.clear_btn)

        self.setLayout(layout)

    def setup_worker(self):
        self.worker.received_message.connect(self.display_message)
        self.worker.connected.connect(self.on_connected)
        self.worker.disconnected.connect(self.on_disconnected)

    def connect_to_server(self):
        url = self.url_input.text()
        if not url:
            self.received_text.append("--- Error: URL cannot be empty ---")
            return
            
        headers = {"Authorization": self.token_input.text(), "tag": self.tag_input.text()}
        self.received_text.append(f"--- Connecting to {url}... ---")
        self.worker.connect(url, headers)

    def disconnect_from_server(self):
        self.worker.disconnect()

    # --- MODIFICATION START ---
    # 3. Updated send_message to construct and send a JSON object
    def send_message(self):
        message_text = self.msg_input.text()
        tag_text = self.tag_input_msg.text()
        
        if message_text:
            # Create a Python dictionary
            payload = {
                "message": message_text,
                "tag": tag_text
            }
            # Convert the dictionary to a JSON string
            json_message = json.dumps(payload)
            
            # Send the JSON string
            self.worker.send(json_message)
            
            # Optionally, show what was sent
            self.received_text.append(f"Sent: {json_message}")
            
            # Clear both input fields
            self.msg_input.clear()
            self.tag_input_msg.clear()
    # --- MODIFICATION END ---

    def display_message(self, msg):
        self.received_text.append(f"Received: {msg}")

    def on_connected(self):
        self.connect_btn.setEnabled(False)
        self.disconnect_btn.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.received_text.append("--- Connected successfully ---")

    def on_disconnected(self, reason=""):
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self.send_btn.setEnabled(False)
        if reason:
            self.received_text.append(f"--- Disconnected: {reason} ---")
        else:
            self.received_text.append("--- Disconnected ---")

    def closeEvent(self, event):
        self.worker.stop_loop()
        self.thread.quit()
        self.thread.wait()
        event.accept()

# ------------------ Run ------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WebSocketClientGUI()
    window.show()
    sys.exit(app.exec_())