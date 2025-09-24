
# 5. Client Integration Guide

This guide explains how a client application (e.g., a web frontend, a mobile app, or an IoT device) can connect to and interact with the Django Real-Time Broker.

## Connection Endpoint

The WebSocket server is accessible at the following URL. Use `ws://` for standard connections and `wss://` for secure connections in production.

`ws://<host>:<port>/ws/brocker/`

## Connection Handshake: Required Headers

To successfully authenticate and establish a connection, the client **must** provide two custom HTTP headers in its initial WebSocket connection request.

#### 1. `Authorization`
This header contains the secret token used to identify and authenticate the client.

-   **Format:** `Token <your_secret_token>`

#### 2. `Tag`
This header contains a comma-separated list of all the tags (topics) the client wishes to subscribe to. The broker will verify that the provided token has `read` or `readwrite` permission for every tag in this list.

-   **Format:** `sensors/+/temp,alerts/#,devices/room1/status`

---

### Connection Example (JavaScript)

Here is an example of how to establish a connection using the standard WebSocket API in a browser environment. Note that some environments or libraries might set headers differently.

```javascript
// --- Configuration ---
const WEBSOCKET_URL = 'ws://localhost:8001/ws/brocker/';
const AUTH_TOKEN = 'your_super_secret_token_here';
const SUBSCRIBED_TAGS = 'sensors/+/temperature,alerts/critical/#';

// --- Create the WebSocket Connection ---
// Note: Standard browser WebSocket API does not support custom headers.
// This example is conceptual. You would need a library like `ReconnectingWebSocket`
// or to handle this in a non-browser environment (e.g., Node.js, Python).
// For a browser, you might pass credentials via query parameters if you modify the backend.

// Conceptual Example for a library that supports headers:
const socket = new WebSocket(WEBSOCKET_URL, {
  headers: {
    'Authorization': `Token ${AUTH_TOKEN}`,
    'Tag': SUBSCRIBED_TAGS
  }
});

// --- Event Handlers ---
socket.onopen = (event) => {
  console.log('Successfully connected to the broker.');
};

socket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(`Received message on tag '${data.tag}':`, data.message);
  // Add your logic here to handle the incoming message
};

socket.onclose = (event) => {
  console.log('Disconnected from broker.', `Code: ${event.code}`, `Reason: ${event.reason}`);
  // Handle disconnection and potential reconnection logic here.
  // See the disconnection codes below.
};

socket.onerror = (error) => {
  console.error('WebSocket Error:', error);
};
```

---

## Message Format

All data messages are sent and received as a single JSON object.

#### Publishing a Message (Client to Server)

To publish a message, the client sends a JSON object with two required keys:

-   `tag` (string): The **specific** topic the message belongs to. This must not contain wildcards. The client's token must have `readwrite` permission for this tag.
-   `message` (any): The payload, which can be any valid JSON (string, number, object, array).

**Example:**
```json
{
  "tag": "sensors/room1/temperature",
  "message": {
    "value": 25.5,
    "unit": "Celsius",
    "timestamp": 1677610000
  }
}
```

#### Receiving a Message (Server to Client)

Messages received from the server follow the exact same format, allowing for consistent parsing on the client-side.

---

## Disconnection Codes

The server uses custom WebSocket close codes to inform the client why a connection was terminated. This allows the client to implement intelligent error handling or reconnection logic.

| Code | Reason                       | Description                                                                                             |
| :--- | :--------------------------- | :------------------------------------------------------------------------------------------------------ |
| `4001` | Missing Credentials          | The `Authorization` or `Tag` header was not provided in the connection request.                         |
| `4003` | Invalid Credentials          | The token is invalid or does not have permission for one or more of the requested tags.                 |
| `4004` | Connection Limit Reached   | The maximum number of concurrent connections for this token has been exceeded.                          |
| `4002` | Token Modified/Revoked       | The client's token was modified or deleted in the database while the client was connected.              |
| `4003` | Permission Revoked/Modified  | A permission affecting one of the client's subscriptions was changed or deleted. *(Uses same code as invalid creds)* |
