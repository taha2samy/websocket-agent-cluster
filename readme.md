# Django Real-Time Broker
![logo](img/logo.png)
<!-- Badges for style points: e.g., Python version, license -->
![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Django Brocker CI/CD](https://github.com/taha2samy/websocket-agent-cluster/actions/workflows/ci.yaml/badge.svg)
![Dependabot Status](https://img.shields.io/badge/Dependabot-up%20to%20date-brightgreen)

A high-performance WebSocket message broker with a dynamic, token-based permission system, built on Django Channels and Redis for real-time security and scalability.
```mermaid
graph TD
    subgraph "External Actors"
        Client[Client IoT/Web]
        Admin[Django Admin]
    end

    subgraph "System Architecture"
        ASGI[ASGI Server ex:Daphne]
        Middleware[AuthMiddlewareBroker]
        Consumer[BrokerConsumer]
        DB[(Postgres/SQLite DB)]
        Signals[Django Signals]
        Redis[Redis Channel Layer]
    end

    %% Connection Flow
    Client -- 1. WebSocket Request (with Token/Tags) --> ASGI
    ASGI -- 2. Forwards to Middleware --> Middleware
    Middleware -- 3a. Auth OK --> Consumer
    Middleware -- 3b. Auth Fail / Limit Reached --> Client
    Consumer -- 4. Subscribes to Groups --> Redis
    Client <--> Consumer

    %% Real-time Security Enforcement Flow
    Admin -- A. Modifies Permission/Token --> DB
    DB -- B. Triggers Signal --> Signals
    Signals -- C. Sends Disconnect Message --> Redis
    Redis -- D. Pushes Message to Consumer --> Consumer
    Consumer -- E. Force Disconnects Client --> Client

    %% Style definitions for clarity
    style Client fill:#2a9d8f,stroke:#fff,stroke-width:2px
    style Admin fill:#e9c46a,stroke:#fff,stroke-width:2px
    style Middleware fill:#f4a261,stroke:#333,stroke-width:2px
    style Consumer fill:#f4a261,stroke:#333,stroke-width:2px
    style Signals fill:#f4a261,stroke:#333,stroke-width:2px
    style Redis fill:#e76f51,stroke:#333,stroke-width:2px

```
---

## Key Features

-   **Secure Authentication:** Token-based access for all WebSocket clients.
-   **Dynamic Permissions:** Granular `read` and `readwrite` permissions for topics.
-   **MQTT-Style Topics:** Flexible topic matching using `+` and `#` wildcards.
-   **Real-Time Security:** Instantly disconnects clients whose permissions are revoked.
-   **Connection Limiting:** Prevents resource abuse with atomic, per-token connection limits.
-   **Scalable:** Built on an ASGI foundation ready for horizontal scaling.

---

## Quick Start

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/taha2samy/websocket-agent-cluster.git .
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure your environment:**
    *   Ensure Redis is running.
    *   Set up your `.env` file based on `.env.example`.

4.  **Run migrations and start the server:**
    ```bash
    python manage.py collectstatic
    python manage.py migrate
    python manage.py runserver
    ```

---

## Full Documentation

For detailed information on architecture, core concepts, and client integration, please see the [**Full Documentation**](./docs/1-introduction.md).
