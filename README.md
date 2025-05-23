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
wait for this message:
 done                                                
Preparing transaction: done                          
Verifying transaction: done                          
Executing transaction: done   
and kafka to start

### Accessing Jupyter Lab

Access Jupyter Lab through either:
- The exposed HTTP service URL: `https://jupyter-[instance-id].http.cloud.morph.so`
- SSH port forwarding: `ssh -L 8888:localhost:8888 [instance-id]@ssh.cloud.morph.so`

# Kubernetes
In a production environment: Install Kubernetes directly on the VM host

```
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt) /bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# Install Minikube
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
chmod +x minikube-linux-amd64
sudo mv minikube-linux-amd64 /usr/local/bin/minikube

# Start Minikube if root --force it
# minikube start --driver=docker --force
# if inside docker for testing
# minikube start --driver=none
# create a user and then start with that user

sudo adduser minikube_user
sudo usermod -aG docker minikube_user
su - minikube_user
minikube start --driver=docker

```
# install go to access kuberneties

First, install the required Go dependencies:
```
# Create a new directory for the project
mkdir -p ~/k8s-check
cd ~/k8s-check

#### install go lang
```
#### Navigate to your project directory
cd ~/k8s-check

#### Initialize the module with proper Go version
go mod init k8s-check

#### Tidy up dependencies and download all required packages
go mod tidy

#### If you still see errors, try forcing the download of all dependencies
go get -u k8s.io/client-go@latest
go get -u k8s.io/apimachinery@latest

#### Run tidy again to resolve any conflicts
go mod tidy

#### Try building again
go build -o k8s-check
```
# check the kubectl working using go lang

```
# Create a corrected simple.go file
cat > simple.go << 'EOF'
package main

import (
	"fmt"
	"os/exec"
)

func main() {
	fmt.Println("Checking Kubernetes/Minikube installation...")
	
	// Check if kubectl is installed
	kubectlCmd := exec.Command("kubectl", "version", "--client")
	kubectlOutput, err := kubectlCmd.CombinedOutput()
	if err != nil {
		fmt.Printf("Error checking kubectl: %v\n", err)
		fmt.Println("kubectl output:", string(kubectlOutput))
	} else {
		fmt.Println("✓ kubectl is installed correctly")
		fmt.Println(string(kubectlOutput))
	}
	
	// Check if minikube is running
	minikubeCmd := exec.Command("minikube", "status")
	minikubeOutput, err := minikubeCmd.CombinedOutput()
	if err != nil {
		fmt.Printf("Error checking minikube: %v\n", err)
		fmt.Println("minikube output:", string(minikubeOutput))
	} else {
		fmt.Println("\n✓ minikube is running")
		fmt.Println(string(minikubeOutput))
	}
	
	// Try to get nodes
	nodesCmd := exec.Command("kubectl", "get", "nodes")
	nodesOutput, err := nodesCmd.CombinedOutput()
	if err != nil {
		fmt.Printf("Error getting nodes: %v\n", err)
		fmt.Println("kubectl output:", string(nodesOutput))
	} else {
		fmt.Println("\n✓ Kubernetes nodes are available:")
		fmt.Println(string(nodesOutput))
	}
}
EOF

# Build the corrected program
go build -o k8s-simple-check simple.go

# Run it
./k8s-simple-check

```

```
#### Create a shell script
cat > check-k8s.sh << 'EOF'
#!/bin/bash

echo "Checking Kubernetes/Minikube installation..."

echo -e "\n=== kubectl version ==="
kubectl version --client || echo "kubectl not installed or not working"

echo -e "\n=== minikube status ==="
minikube status || echo "minikube not running"

echo -e "\n=== Kubernetes nodes ==="
kubectl get nodes || echo "Cannot get nodes"

echo -e "\n=== Kubernetes pods ==="
kubectl get pods --all-namespaces || echo "Cannot get pods"
EOF

#### Make it executable
chmod +x check-k8s.sh

#### Run it
./check-k8s.sh

```
Or
```
#### Create a shell script
cat > check-k8s.sh << 'EOF'
#!/bin/bash

echo "Checking Kubernetes/Minikube installation..."

echo -e "\n=== kubectl version ==="
kubectl version --client || echo "kubectl not installed or not working"

echo -e "\n=== minikube status ==="
minikube status || echo "minikube not running"

echo -e "\n=== Kubernetes nodes ==="
kubectl get nodes || echo "Cannot get nodes"

echo -e "\n=== Kubernetes pods ==="
kubectl get pods --all-namespaces || echo "Cannot get pods"
EOF

#### Make it executable
chmod +x check-k8s.sh

#### Run it
./check-k8s.sh

```
#These commands will help you verify that your Kubernetes cluster is functioning correctly without needing Go.
```
#### Check if minikube is running
minikube status

#### Get cluster information
kubectl cluster-info

#### List all nodes
kubectl get nodes

#### Create a test deployment
kubectl create deployment hello-minikube --image=k8s.gcr.io/echoserver:1.10

#### Expose the deployment
kubectl expose deployment hello-minikube --type=NodePort --port=8080

#### Check if the pod is running
kubectl get pods

#### Get the URL to access the service
minikube service hello-minikube --url
```

# Initialize Go module
go mod init k8s-check

# Install required dependencies
go get k8s.io/client-go@latest
go get k8s.io/apimachinery@latest

```

# Trading Environment Docker Setup
```

scp build_env.sh to the morph VM instance 
scp build_env.zip  <morph_instance>@ssh.cloud.morph.so:~/
on VM
unzip build_env.zip
docker-compose up --build
docker-compose down
docker-compose up -d

```

Then enter the Docker container 
```

# First, find your container ID
docker ps

# Then enter the container
docker exec -it CONTAINER_ID bash

# Now you can use Python and Conda inside the container
python --version
conda --version

```


This repository contains a dockerized environment for algorithmic trading development with Conda, Kafka, and Vertica integration. It's designed to be used with Morph.so cloud for creating standardized snapshots that can be easily deployed.

More products can be added.


# Pods
In a Kubernetes environment, NATS.io and Weaviate would be deployed as pods, but they would typically be managed by Deployments and exposed via Services.

..

## Kubernetes in Docker Environment -- STEP 1

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



## Manually set up NATS and Kubernetes in your Docker environment. Here's a step-by-step guide 

### Setting up Kubernetes (Minikube) in Docker
#### 1. Install Docker prerequisites:
```
docker run -d \
  --name minikube-prerequisites \
  --network morph-network \
  ubuntu:22.04 \
  tail -f /dev/null

docker exec minikube-prerequisites apt-get update
docker exec minikube-prerequisites apt-get install -y curl apt-transport-https

```
### Install kubectl in the container:
```

docker exec minikube-prerequisites bash -c "curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64"
docker exec minikube-prerequisites bash -c "chmod +x minikube-linux-amd64 && mv minikube-linux-amd64 /usr/local/bin/minikube"

```
### Install Minikube in the container:
```
docker exec minikube-prerequisites bash -c "curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64"
docker exec minikube-prerequisites bash -c "chmod +x minikube-linux-amd64 && mv minikube-linux-amd64 /usr/local/bin/minikube"

```
### Start Minikube with Docker driver:

# First, install Docker in the container
```
docker exec minikube-prerequisites apt-get install -y docker.io


# Start Minikube
docker exec minikube-prerequisites bash -c "minikube start --driver=docker"

### Verify Kubernetes installation:

docker exec minikube-prerequisites kubectl get nodes
docker exec minikube-prerequisites minikube status
```

# Setting up NATS in Docker
### Create a Docker network (if you don't already have one):
```
docker network create morph-network

### Create directories for NATS data and configuration:

mkdir -p ~/nats/config
mkdir -p ~/nats/data/jetstream

### Create a NATS configuration file:

cat > ~/nats/config/nats-server.conf << EOF

# NATS Server Configuration

port: 4222
http_port: 8222
server_name: nats-server

# JetStream configuration

jetstream {
    store_dir: "/data/jetstream"
    max_mem: 1G
    max_file: 10G
}

# Logging configuration

debug: false
trace: false
logtime: true
EOF
```
### Run NATS container:
```
docker run -d \
  --name nats-server \
  --network morph-network \
  -p 4222:4222 \
  -p 8222:8222 \
  -p 6222:6222 \
  -v ~/nats/config:/etc/nats \
  -v ~/nats/data/jetstream:/data/jetstream \
  nats:2.9.17 \
  -c /etc/nats/nats-server.conf
```
### Verify NATS is running:
```
docker logs nats-server
```
# Check NATS monitoring endpoint
```
curl http://localhost:8222
```
### Integrating NATS with Kubernetes
# Create a NATS deployment in Kubernetes:
```
docker exec minikube-prerequisites bash -c "cat > nats-deployment.yaml << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nats
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nats
  template:
    metadata:
      labels:
        app: nats
    spec:
      containers:
      - name: nats
        image: nats:2.9.17
        ports:
        - containerPort: 4222
          name: client
        - containerPort: 8222
          name: monitoring
        - containerPort: 6222
          name: cluster
---
apiVersion: v1
kind: Service
metadata:
  name: nats
spec:
  selector:
    app: nats
  ports:
  - name: client
    port: 4222
    targetPort: 4222
  - name: monitoring
    port: 8222
    targetPort: 8222
  - name: cluster
    port: 6222
    targetPort: 6222
EOF"

docker exec minikube-prerequisites kubectl apply -f nats-deployment.yaml

```
### Verify NATS is running in Kubernetes:
```
docker exec minikube-prerequisites kubectl get pods
docker exec minikube-prerequisites kubectl get services

```
### Access NATS from within Kubernetes:
```
docker exec minikube-prerequisites bash -c "kubectl run -i --tty nats-box --image=natsio/nats-box --restart=Never -- sh"

```
### Inside the nats-box pod, you can run:
```
# Connect to NATS server
nats-sub -s nats://nats:4222 ">"

```

### Integrating Weaviate with Kubernetes


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
