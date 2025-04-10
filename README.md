# Morph.so Minimal Trading Environment Setup

## Overview

This README provides instructions for setting up a minimal trading environment on Morph.so with Docker, Conda, Kafka, Vertica, and Jupyter Lab. This optimized setup focuses on essential components for algorithm development and simulation while excluding time-consuming installations like Kubernetes, C++, and Go.

## Components Included

- **Docker & Docker Compose**: Container platform for running isolated environments
- **Conda**: Python package and environment management system
- **Kafka**: Distributed event streaming platform for high-throughput data pipelines
- **Vertica Client**: Analytics database client for high-performance data processing
- **Jupyter Lab**: Interactive development environment for data analysis and visualization

## Directory Structure

```
/root/trading_env/          # Base directory for all components
├── data/                   # Directory for persistent data storage
├── notebooks/              # Directory for Jupyter notebooks
├── docker-compose.yml      # Docker Compose configuration
├── Dockerfile              # Docker container definition
├── start.sh                # Startup script for services
└── test_environments.sh    # Script to verify installations
```

## Installation Process

The installation process follows these steps:

1. **VM Creation**: Creates a Morph.so VM with specified resources (4 vCPUs, 8GB RAM, 50GB disk)
2. **Directory Setup**: Creates the directory structure for organizing files
3. **Host Tools Installation**: Installs Python and Conda directly on the host VM
4. **Docker Installation**: Installs Docker and Docker Compose on the host VM
5. **Docker Environment Setup**: Creates and builds Docker containers with Conda, Kafka, and Vertica
6. **Service Exposure**: Exposes Jupyter Lab for external access
7. **Snapshot Creation**: Creates a snapshot of the fully configured environment

## Usage Instructions

### Starting the Environment

```bash
# Start Docker containers
cd /root/trading_env
docker-compose up -d
```

### Accessing Jupyter Lab

Access Jupyter Lab through either:
- The exposed HTTP service URL: `https://jupyter-[instance-id].http.cloud.morph.so`
- SSH port forwarding: `ssh -L 8888:localhost:8888 [instance-id]@ssh.cloud.morph.so`

### Working with Kafka

```bash
# Create a topic
docker exec trading-environment $KAFKA_HOME/bin/kafka-topics.sh --create --topic my-topic --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1

# Produce messages
docker exec -it trading-environment $KAFKA_HOME/bin/kafka-console-producer.sh --topic my-topic --bootstrap-server localhost:9092

# Consume messages
docker exec -it trading-environment $KAFKA_HOME/bin/kafka-console-consumer.sh --topic my-topic --from-beginning --bootstrap-server localhost:9092
```

### Vertica Client Usage

```python
# Python example for connecting to Vertica
import vertica_python

conn_info = {
    'host': 'your_vertica_host',
    'port': 5433,
    'user': 'your_username',
    'password': 'your_password',
    'database': 'your_database'
}

with vertica_python.connect(**conn_info) as connection:
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM your_table LIMIT 10')
    for row in cursor.fetchall():
        print(row)
```

## Kubernetes in Docker Environment

While not included in this minimal setup, Kubernetes can be added later to provide container orchestration capabilities. In a Morph.so environment, Kubernetes (via minikube) operates in a nested virtualization arrangement:

Docker containers run directly on the Morph.so VM, while Kubernetes creates its own virtualized cluster inside Docker containers. This architecture allows Kubernetes pods to run inside Docker containers that themselves run on the VM. When configured, minikube uses Docker as its driver, creating a virtual Kubernetes node as a Docker container. The Kubernetes control plane components run inside this container, and Docker's networking is used to expose Kubernetes services. This approach provides a complete development environment where you can test both simple Docker deployments and complex Kubernetes orchestrations on the same Morph.so instance.

## Extending the Environment

To add additional components later:

1. Start an instance from your minimal snapshot
2. Install only the components you need:
   ```bash
   apt-get update
   apt-get install -y kubectl minikube  # For Kubernetes
   apt-get install -y build-essential   # For C++
   ```
3. Create a new snapshot of the extended environment

## Troubleshooting

- **Docker Issues**: Verify Docker is running with `systemctl status docker`
- **Jupyter Access**: Ensure port 8888 is properly exposed and not blocked
- **Kafka Connection**: Check Kafka logs with `docker-compose logs`
- **Permission Issues**: Remember that the default user is 'root', not 'ubuntu'

## Resource Optimization

For better performance:
- Increase VM resources (vCPUs, memory) in the configuration
- Use Docker volume mounts for data persistence
- Regularly clean up unused Docker images and containers

## License
dronomy.io
