# 2. Getting Started

This guide provides step-by-step instructions to set up the project for local development and get the server running.

## Prerequisites

Before you begin, ensure you have the following software installed on your system:

-   **Python 3.10+**
-   **Redis 6.0+** (The broker's channel layer depends on Redis)
-   **Git**

## Installation & Setup

Follow these steps to get a local development environment running.

### 1. Clone the Repository

First, clone the project repository from GitHub to your local machine.

```bash
git clone https://github.com/your-username/your-project.git
cd your-project


### 2. Create a Virtual Environment

It is a best practice to use a virtual environment to manage project dependencies.

```bash
# Create the environment
python -m venv venv

# Activate the environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

Install all the required Python packages using the `requirements.txt` file.

```bash
pip install -r requirements.txt
```

## Configuration

The project's configuration is managed using environment variables.

### 1. Set Up the `.env` File

Copy the provided example file to create your local configuration file.

```bash
cp .env.example .env
```

Now, open the `.env` file with a text editor and set the required variables:

-   `SECRET_KEY`: A strong, unique secret key for your Django application. You can generate one easily online.
-   `DEBUG`: Set to `True` for development mode, which provides detailed error pages. Set to `False` in production.
-   `REDIS_URL`: The connection URL for your Redis instance. The default for a local installation is typically `redis://localhost:6379/1`.

### 2. Prepare the Database

Run the initial database migrations to create the necessary tables for the application models.

```bash
python manage.py migrate
```

### 3. Create an Administrator

To access the Django admin panel and manage tokens, tags, and permissions, you need to create a superuser.

```bash
python manage.py createsuperuser
```
You will be prompted to enter a username, email, and password.

## Running the Application

This is an ASGI application and requires an ASGI server like Daphne to run.

```bash
# Run the server on port 8001
daphne -p 8001 project_name.asgi:application
```

> **Note:** Replace `project_name` with the actual name of your Django project directory (the one containing `settings.py`).

Your real-time broker is now running! The WebSocket endpoint is accessible at:
**`ws://localhost:8001/ws/brocker/`**
