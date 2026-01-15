# Standalone Redis Container Setup

This directory contains the Docker configuration for running a Redis in-memory database container.
This setup allows you to run Redis in a self-contained environment for conversation history storage,
session management, and caching.

## Prerequisites

- Docker installed on your system
- Sufficient disk space for data persistence (AOF enabled)

## Building the Image

Navigate to the `redis` directory containing the Dockerfile, then build the Docker image:

```bash
cd redis
docker build -t redis-custom:latest .
```

## Running the Container

Run the container from the built image with the following command:

```bash
docker run -d \
  --name custom-redis-container \
  -p 6379:6379 \
  -v redis_data:/data \
  redis-custom:latest
```

## Using Redis CLI

Connect to Redis using the CLI:

```bash
redis-cli -p 6379
```

## Data Persistence

This container uses AOF (Append-Only File) for data persistence. Data is automatically saved to disk.

- Check memory usage:
```bash
redis-cli INFO memory
```

- Monitor live commands:
```bash
redis-cli MONITOR
```

## Use Cases

- **Conversation History**: Store chat session data with TTL auto-expiration
- **Session Management**: Track user sessions and context
- **Caching**: Cache search results and embeddings temporarily
- **Message Queue**: Optional pub/sub for real-time features

## Configuration

The container runs with:
- Port: 6379 (standard Redis port)
- Persistence: AOF enabled (`--appendonly yes`)
- Volume: `/data` for persistent storage

To modify settings, edit the `CMD` in the Dockerfile or pass arguments to `redis-server`.

## Docker Compose Integration

This container is managed by `docker-compose.yaml` at the project root.

Start all services:
```bash
docker-compose up -d
```

Stop all services:
```bash
docker-compose down
```
