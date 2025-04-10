# NATS.io Integration for Morph.so Environment

This document provides detailed information about the NATS.io integration in the Morph.so environment setup.

## Overview

NATS.io is a simple, secure, and high-performance messaging system for cloud native applications, IoT messaging, and microservices architectures. This integration adds NATS.io to the Morph.so environment, allowing you to use it for event streaming, service communication, and persistent messaging.

## Features

- **NATS Server**: Core NATS messaging system
- **JetStream**: Persistent messaging with stream processing
- **Python Client**: Ready-to-use Python client for NATS
- **Example Scripts**: Sample code for publishing and subscribing
- **Docker Integration**: NATS available in Docker containers
- **Monitoring**: Web-based monitoring interface

## Configuration

The NATS configuration is defined in the `NATS_CONFIG` section of the configuration files:

```python
NATS_CONFIG = {
    "version": "2.9.17",  # Latest stable version
    "client_port": 4222,   # Port for client connections
    "http_port": 8222,     # Port for HTTP monitoring
    "routing_port": 6222,  # Port for clustering
    "install_nats_py": True,  # Install Python client
    "cluster_name": "trading_cluster",
    "jetstream_enabled": True,  # Enable persistent messaging
}
```

## Usage

### Basic Messaging

NATS follows a publish-subscribe model. Here's how to use it with the provided Python examples:

1. **Subscribe to a subject**:
   ```bash
   python /root/trading_env/nats/examples/nats-sub.py my-subject
   ```

2. **Publish to a subject**:
   ```bash
   python /root/trading_env/nats/examples/nats-pub.py my-subject -d "Hello World"
   ```

3. **Using queue groups** (load balancing):
   ```bash
   # Start multiple subscribers in the same queue group
   python /root/trading_env/nats/examples/nats-sub.py my-subject -q worker-group
   ```

### JetStream (Persistent Messaging)

JetStream provides persistence for NATS messages:

1. **Create a stream**:
   ```bash
   python /root/trading_env/nats/examples/jetstream.py --create
   ```

2. **Publish messages**:
   ```bash
   python /root/trading_env/nats/examples/jetstream.py --publish
   ```

3. **Subscribe to messages**:
   ```bash
   python /root/trading_env/nats/examples/jetstream.py --subscribe
   ```

### Monitoring

NATS provides a built-in monitoring interface:

- **Web Interface**: Access at http://localhost:8222 when running locally
- **Remote Access**: Available at https://nats-monitor-[instance-id].http.cloud.morph.so when exposed

### Using NATS in Your Applications

To use NATS in your own Python applications:

```python
import asyncio
from nats.aio.client import Client as NATS

async def main():
    # Connect to NATS
    nc = NATS()
    await nc.connect("nats://localhost:4222")
    
    # Define a message handler
    async def message_handler(msg):
        subject = msg.subject
        data = msg.data.decode()
        print(f"Received message on {subject}: {data}")
    
    # Subscribe to a subject
    await nc.subscribe("my.subject", cb=message_handler)
    
    # Publish a message
    await nc.publish("my.subject", b"Hello from NATS!")
    
    # Keep the connection open
    await asyncio.sleep(10)
    
    # Close the connection
    await nc.close()

if __name__ == "__main__":
    asyncio.run(main())
```

## Docker Integration

The NATS server is integrated into the Docker environment:

- **Ports**: 4222 (client), 8222 (monitoring), 6222 (clustering)
- **Volumes**: Configuration and JetStream data are persisted
- **Startup**: NATS starts automatically with the Docker container

## Advanced Configuration

### Custom NATS Configuration

You can customize the NATS server configuration by editing:
```
/root/trading_env/nats/config/nats-server.conf
```

Common configuration options:

```
# Basic server configuration
port: 4222
http: 8222

# Logging
debug: false
trace: false

# Security (uncomment to enable)
# authorization {
#   user: nats
#   password: password
# }

# Clustering
cluster {
  name: trading_cluster
  port: 6222
}

# JetStream
jetstream {
  store_dir: "/var/lib/nats/jetstream"
  max_mem: 1G
  max_file: 10G
}
```

### Running NATS as a Service

NATS is configured as a systemd service for automatic startup:

```bash
# Start NATS service
systemctl start nats-server

# Check status
systemctl status nats-server

# Enable automatic startup
systemctl enable nats-server
```

## Troubleshooting

### Common Issues

1. **Connection Refused**:
   - Check if NATS server is running: `nats server check`
   - Verify the port is correct: `netstat -tuln | grep 4222`

2. **Permission Denied**:
   - Check JetStream directory permissions: `ls -la /var/lib/nats/jetstream`
   - Fix with: `chmod -R 777 /var/lib/nats`

3. **Docker Container Issues**:
   - Check logs: `docker logs trading-environment`
   - Restart container: `docker restart trading-environment`

### Useful Commands

- **Check NATS server info**: `nats server info`
- **List streams**: `nats stream ls`
- **View stream info**: `nats stream info STREAMNAME`
- **Publish message**: `nats pub subject "message"`
- **Subscribe to messages**: `nats sub subject`

## Resources

- [NATS Documentation](https://docs.nats.io/)
- [NATS Python Client](https://github.com/nats-io/nats.py)
- [JetStream Documentation](https://docs.nats.io/nats-concepts/jetstream)
