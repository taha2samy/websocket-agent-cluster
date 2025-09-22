import asyncio
import websockets
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading

class WebSocketClientApp:
    def __init__(self, root):
        self.root = root
        self.root.title("WebSocket TTK Client")

        # WebSocket connection
        self.websocket = None
        self.loop = asyncio.new_event_loop()
        
        # Set up GUI elements
        self.setup_gui()
        
        # Start the asyncio event loop in a background thread
        threading.Thread(target=self.run_event_loop, daemon=True).start()

    def run_event_loop(self):
        """Run the asyncio event loop in a separate thread."""
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def setup_gui(self):
        """Set up the GUI elements."""
        # Header Section
        socket_frame = ttk.LabelFrame(self.root, text="socket", padding=(10, 10))
        socket_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        ttk.Label(socket_frame, text="IP:").grid(row=0, column=0, sticky="w")
        ttk.Label(socket_frame, text="Port:").grid(row=0, column=2)
        self.ip = ttk.Entry(socket_frame, width=30)
        self.ip.grid(row=0, column=1, padx=5, pady=5)
        self.port = ttk.Entry(socket_frame, width=10)  
        self.port.grid(row=0, column=3, padx=5, pady=5)
        headers_frame = ttk.LabelFrame(self.root, text="Headers", padding=(10, 10))
        headers_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        
        ttk.Label(headers_frame, text="Token:").grid(row=0, column=0, sticky="w")
        self.token_entry = ttk.Entry(headers_frame, width=30)
        self.token_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(headers_frame, text="Tags (comma-separated):").grid(row=1, column=0, sticky="w")
        self.tag_entry = ttk.Entry(headers_frame, width=30)
        self.tag_entry.grid(row=1, column=1, padx=5, pady=5)

        # Connection Buttons
        self.connect_button = ttk.Button(headers_frame, text="Connect", command=self.connect_to_server)
        self.connect_button.grid(row=2, column=0, padx=5, pady=5, sticky="w")

        self.disconnect_button = ttk.Button(headers_frame, text="Disconnect", command=self.disconnect_from_server, state="disabled")
        self.disconnect_button.grid(row=2, column=1, padx=5, pady=5, sticky="e")

        # Message Section
        message_frame = ttk.LabelFrame(self.root, text="Message", padding=(10, 10))
        message_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        
        ttk.Label(message_frame, text="Enter Message:").grid(row=0, column=0, sticky="w")
        self.message_entry = ttk.Entry(message_frame, width=40)
        self.message_entry.grid(row=0, column=1, padx=5, pady=5)
        
        self.send_button = ttk.Button(message_frame, text="Send Message", command=self.send_message, state="disabled")
        self.send_button.grid(row=1, column=0, columnspan=2, pady=5)

        # Received Messages Section
        received_frame = ttk.LabelFrame(self.root, text="Received Messages", padding=(10, 10))
        received_frame.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        
        self.received_text = scrolledtext.ScrolledText(received_frame, width=50, height=10, state='disabled')
        self.received_text.grid(row=0, column=0, padx=5, pady=5)

        # Clear Messages Button
        self.clear_button = ttk.Button(received_frame, text="Clear Messages", command=self.clear_messages)
        self.clear_button.grid(row=1, column=0, padx=5, pady=5, sticky="e")

    async def connect(self):
        """Establish a WebSocket connection to the server."""
        ip =self.ip.get()
        port = self.port.get()
        url=f"ws://{ip}:{port}"
        headers = {
            "Authorization": self.token_entry.get(),
            "tag": self.tag_entry.get()
        }
        try:
            self.websocket = await websockets.connect(url, extra_headers=headers)
            self.update_connection_state(True)
            await self.receive_messages()
        except Exception as e:
            messagebox.showerror("Connection Error", f"Could not connect to the server: {e}")

    def connect_to_server(self):
        """Initiate connection to the WebSocket server."""
        asyncio.run_coroutine_threadsafe(self.connect(), self.loop)

    async def receive_messages(self):
        """Continuously receive messages from the WebSocket server."""
        try:
            while True:
                message = await self.websocket.recv()
                self.display_received_message(message)
        except websockets.ConnectionClosed:
            messagebox.showinfo("Disconnected", "Connection closed by the server.")
            self.update_connection_state(False)

    def display_received_message(self, message):
        """Display a received message in the text box."""
        self.received_text.config(state='normal')
        self.received_text.insert(tk.END, f"Received: {message}\n")
        self.received_text.config(state='disabled')
        self.received_text.yview(tk.END)

    async def send(self):
        """Send a message to the WebSocket server."""
        message = self.message_entry.get()
        if self.websocket and message:
            await self.websocket.send(message)
            self.message_entry.delete(0, tk.END)

    def send_message(self):
        """Send a message when the button is pressed."""
        asyncio.run_coroutine_threadsafe(self.send(), self.loop)

    async def disconnect(self):
        """Disconnect from the WebSocket server."""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            self.update_connection_state(False)

    def disconnect_from_server(self):
        """Initiate disconnection from the WebSocket server."""
        asyncio.run_coroutine_threadsafe(self.disconnect(), self.loop)

    def update_connection_state(self, connected):
        """Update the state of buttons based on the connection state."""
        if connected:
            self.connect_button.config(state="disabled")
            self.disconnect_button.config(state="normal")
            self.send_button.config(state="normal")
        else:
            self.connect_button.config(state="normal")
            self.disconnect_button.config(state="disabled")
            self.send_button.config(state="disabled")

    def clear_messages(self):
        """Clear the received messages from the display."""
        self.received_text.config(state='normal')
        self.received_text.delete('1.0', tk.END)
        self.received_text.config(state='disabled')

if __name__ == "__main__":
    root = tk.Tk()
    app = WebSocketClientApp(root)
    root.mainloop()