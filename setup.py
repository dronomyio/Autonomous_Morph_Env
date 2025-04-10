#!/usr/bin/env python3
"""
Modular setup script for Morph.so environments.

This script creates a customizable Morph.so environment with support for:
- Docker and Docker Compose
- Conda for Python package management
- Kafka for event streaming
- Vertica client for database access
- Kubernetes (minikube) for container orchestration
- C++ development environment
- Go programming language
- Jupyter Lab for interactive development

Usage:
    python setup.py [--config CONFIG_FILE]
"""

import os
import sys
import time
import argparse
from importlib.util import spec_from_file_location, module_from_spec

# Default configuration file
DEFAULT_CONFIG = os.path.join(os.path.dirname(__file__), "config.py")

def load_config(config_file):
    """Load configuration from a Python file."""
    try:
        spec = spec_from_file_location("config", config_file)
        config = module_from_spec(spec)
        spec.loader.exec_module(config)
        return config
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Modular setup script for Morph.so environments")
    parser.add_argument("--config", default=DEFAULT_CONFIG, help="Path to configuration file")
    return parser.parse_args()

class MorphSetup:
    """Main class for setting up Morph.so environments."""
    
    def __init__(self, config):
        """Initialize with configuration."""
        self.config = config
        # Check for Morph API key
        if "MORPH_API_KEY" not in os.environ:
            print("Error: MORPH_API_KEY environment variable not set")
            print("Please set it with: export MORPH_API_KEY='your-api-key-here'")
            sys.exit(1)
        
        # Import Morph Cloud client
        try:
            from morphcloud.api import MorphCloudClient
            self.client = MorphCloudClient()
        except ImportError:
            print("Error: morphcloud package not installed")
            print("Please install it with: pip install morphcloud")
            sys.exit(1)
        
        self.instance = None
        self.snapshot = None
        
        # Get username from config
        self.username = self.config.VM_CONFIG.get("username", "root")
        print(f"Using username: {self.username}")
    
    def create_vm(self):
        """Create a base VM in Morph.so."""
        print("Creating base VM in Morph.so...")
        self.snapshot = self.client.snapshots.create(
            image_id=self.config.VM_CONFIG["image_id"],
            vcpus=self.config.VM_CONFIG["vcpus"],
            memory=self.config.VM_CONFIG["memory"],
            disk_size=self.config.VM_CONFIG["disk_size"]
        )
        print(f"✓ Created snapshot: {self.snapshot.id}")
        
        # Start an instance from the snapshot
        print("Starting instance...")
        self.instance = self.client.instances.start(self.snapshot.id)
        print(f"✓ Started instance: {self.instance.id}")
    
    def setup_directories(self, ssh):
        """Set up directory structure on the VM."""
        print("Setting up directory structure...")
        for dir_name, dir_path in self.config.DIR_CONFIG.items():
            print(f"  - Creating {dir_name} directory: {dir_path}")
            ssh.run(f"mkdir -p {dir_path}").raise_on_error()
    
    def install_host_tools(self, ssh):
        """Install tools directly on the host VM."""
        print("Setting up host environment...")
        
        # Update package lists
        print("  - Updating package lists...")
        ssh.run("apt-get update").raise_on_error()
        
        # Install Python if enabled
        if self.config.MODULE_CONFIG["install_conda"]:
            print("  - Installing Python on host VM...")
            ssh.run("apt-get install -y python3 python3-pip").raise_on_error()
            ssh.run("ln -sf /usr/bin/python3 /usr/bin/python").raise_on_error()
            
            # Install Miniconda on host
            print("  - Installing Miniconda on host VM...")
            ssh.run("wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh").raise_on_error()
            ssh.run("bash /tmp/miniconda.sh -b -p /opt/conda").raise_on_error()
            
            # Add to bashrc for both root and the configured user
            ssh.run("echo 'export PATH=\"/opt/conda/bin:$PATH\"' >> /root/.bashrc").raise_on_error()
            
            # Check if user exists before adding to their bashrc
            if self.username != "root":
                # Use a safer approach to check if user exists
                result = ssh.run(f"id -u {self.username} &>/dev/null && echo 'exists' || echo 'not exists'")
                # Check if the command output contains 'exists' - using str() to safely convert to string
                if 'exists' in str(result):
                    ssh.run(f"echo 'export PATH=\"/opt/conda/bin:$PATH\"' >> /home/{self.username}/.bashrc").raise_on_error()
            
            # Make conda available in current session
            ssh.run("export PATH=\"/opt/conda/bin:$PATH\"").raise_on_error()
            
            # Verify Python and Conda installation
            print("  - Verifying Python and Conda installation...")
            ssh.run("python --version").raise_on_error()
            ssh.run("/opt/conda/bin/conda --version").raise_on_error()
    
    def install_docker(self, ssh):
        """Install Docker and Docker Compose on the VM."""
        if not self.config.MODULE_CONFIG["install_docker"]:
            return
        
        print("Installing Docker and Docker Compose...")
        ssh.run("apt-get install -y docker.io docker-compose").raise_on_error()
        
        # Start and enable Docker
        print("  - Starting Docker service...")
        ssh.run("systemctl start docker").raise_on_error()
        ssh.run("systemctl enable docker").raise_on_error()
        
        # Add user to Docker group - only if the user exists and is not root
        if self.username != "root":
            print(f"  - Checking if user {self.username} exists...")
            result = ssh.run(f"id -u {self.username} &>/dev/null && echo 'exists' || echo 'not exists'")
            # Check if the command output contains 'exists' - using str() to safely convert to string
            if 'exists' in str(result):
                print(f"  - Adding user {self.username} to docker group...")
                ssh.run(f"usermod -aG docker {self.username}").raise_on_error()
            else:
                print(f"  - Warning: User '{self.username}' does not exist, skipping group addition")
        else:
            print("  - Using root user, no need to add to docker group")
        
        # Verify Docker installation
        print("  - Verifying Docker installation...")
        ssh.run("docker --version").raise_on_error()
        ssh.run("docker-compose --version").raise_on_error()
    
    def install_kubernetes(self, ssh):
        """Install Kubernetes (minikube) on the VM."""
        if not self.config.MODULE_CONFIG["install_kubernetes"]:
            return
        
        print("Installing Kubernetes tools...")
        
        # Install kubectl
        if self.config.KUBERNETES_CONFIG["install_kubectl"]:
            print("  - Installing kubectl...")
            ssh.run("curl -LO https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl").raise_on_error()
            ssh.run("chmod +x kubectl").raise_on_error()
            ssh.run("mv kubectl /usr/local/bin/").raise_on_error()
            
            # Verify kubectl installation
            ssh.run("kubectl version --client").raise_on_error()
        
        # Install minikube
        if self.config.KUBERNETES_CONFIG["install_minikube"]:
            print("  - Installing minikube...")
            ssh.run(f"curl -LO https://storage.googleapis.com/minikube/releases/v{self.config.KUBERNETES_CONFIG['version']}/minikube-linux-amd64").raise_on_error()
            ssh.run("chmod +x minikube-linux-amd64").raise_on_error()
            ssh.run("mv minikube-linux-amd64 /usr/local/bin/minikube").raise_on_error()
            
            # Verify minikube installation
            ssh.run("minikube version").raise_on_error()
        
        # Install Helm
        if self.config.KUBERNETES_CONFIG["install_helm"]:
            print("  - Installing Helm...")
            ssh.run("curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash").raise_on_error()
            
            # Verify Helm installation
            ssh.run("helm version").raise_on_error()
        
        # Create Kubernetes configuration directory
        print("  - Setting up Kubernetes configuration...")
        ssh.run(f"mkdir -p {self.config.DIR_CONFIG['kubernetes_dir']}/manifests").raise_on_error()
    
    def install_cpp(self, ssh):
        """Install C++ development environment on the VM."""
        if not self.config.MODULE_CONFIG["install_cpp"]:
            return
        
        print("Installing C++ development environment...")
        
        # Install GCC/G++
        if self.config.LANGUAGES_CONFIG["cpp"]["install_gcc"]:
            print("  - Installing GCC/G++...")
            gcc_version = self.config.LANGUAGES_CONFIG["cpp"]["gcc_version"]
            ssh.run(f"apt-get install -y build-essential gcc-{gcc_version} g++-{gcc_version}").raise_on_error()
            
            # Set as default compiler
            ssh.run(f"update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-{gcc_version} 100").raise_on_error()
            ssh.run(f"update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-{gcc_version} 100").raise_on_error()
            
            # Verify GCC/G++ installation
            ssh.run("gcc --version").raise_on_error()
            ssh.run("g++ --version").raise_on_error()
        
        # Install CMake
        if self.config.LANGUAGES_CONFIG["cpp"]["install_cmake"]:
            print("  - Installing CMake...")
            ssh.run("apt-get install -y cmake").raise_on_error()
            
            # Verify CMake installation
            ssh.run("cmake --version").raise_on_error()
        
        # Create C++ project directory
        print("  - Setting up C++ project directory...")
        ssh.run(f"mkdir -p {self.config.DIR_CONFIG['cpp_dir']}/projects").raise_on_error()
        
        # Create a simple C++ test project
        print("  - Creating C++ test project...")
        cpp_test_dir = f"{self.config.DIR_CONFIG['cpp_dir']}/projects/hello_world"
        ssh.run(f"mkdir -p {cpp_test_dir}").raise_on_error()
        
        # Create main.cpp
        main_cpp = """#include <iostream>

int main() {
    std::cout << "Hello, World from C++ on Morph.so!" << std::endl;
    return 0;
}
"""
        ssh.run(f"echo '{main_cpp}' > {cpp_test_dir}/main.cpp").raise_on_error()
        
        # Create CMakeLists.txt
        cmake_lists = """cmake_minimum_required(VERSION 3.10)
project(HelloWorld)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_executable(hello_world main.cpp)
"""
        ssh.run(f"echo '{cmake_lists}' > {cpp_test_dir}/CMakeLists.txt").raise_on_error()
        
        # Create build script
        build_script = """#!/bin/bash
mkdir -p build
cd build
cmake ..
make
"""
        ssh.run(f"echo '{build_script}' > {cpp_test_dir}/build.sh").raise_on_error()
        ssh.run(f"chmod +x {cpp_test_dir}/build.sh").raise_on_error()
    
    def install_go(self, ssh):
        """Install Go programming language on the VM."""
        if not self.config.MODULE_CONFIG["install_go"]:
            return
        
        print("Installing Go programming language...")
        go_version = self.config.LANGUAGES_CONFIG["go"]["version"]
        
        # Download and install Go
        print(f"  - Installing Go {go_version}...")
        ssh.run(f"wget https://go.dev/dl/go{go_version}.linux-amd64.tar.gz -O /tmp/go.tar.gz").raise_on_error()
        ssh.run("tar -C /usr/local -xzf /tmp/go.tar.gz").raise_on_error()
        ssh.run("rm /tmp/go.tar.gz").raise_on_error()
        
        # Set up Go environment
        print("  - Setting up Go environment...")
        ssh.run("echo 'export PATH=$PATH:/usr/local/go/bin' >> /etc/profile").raise_on_error()
        ssh.run("echo 'export PATH=$PATH:/usr/local/go/bin' >> /root/.bashrc").raise_on_error()
        
        # Add to user's bashrc if the user exists and is not root
        if self.username != "root":
            result = ssh.run(f"id -u {self.username} &>/dev/null && echo 'exists' || echo 'not exists'")
            # Check if the command output contains 'exists' - using str() to safely convert to string
            if 'exists' in str(result):
                ssh.run(f"echo 'export PATH=$PATH:/usr/local/go/bin' >> /home/{self.username}/.bashrc").raise_on_error()
        
        ssh.run("export PATH=$PATH:/usr/local/go/bin").raise_on_error()
        
        # Verify Go installation
        print("  - Verifying Go installation...")
        ssh.run("/usr/local/go/bin/go version").raise_on_error()
        
        # Create Go project directory
        print("  - Setting up Go project directory...")
        go_dir = self.config.DIR_CONFIG["go_dir"]
        ssh.run(f"mkdir -p {go_dir}/projects").raise_on_error()
        
        # Create a simple Go test project
        print("  - Creating Go test project...")
        go_test_dir = f"{go_dir}/projects/hello_world"
        ssh.run(f"mkdir -p {go_test_dir}").raise_on_error()
        
        # Create main.go
        main_go = """package main

import "fmt"

func main() {
    fmt.Println("Hello, World from Go on Morph.so!")
}
"""
        ssh.run(f"echo '{main_go}' > {go_test_dir}/main.go").raise_on_error()
        
        # Create build script
        build_script = """#!/bin/bash
/usr/local/go/bin/go build -o hello_world main.go
"""
        ssh.run(f"echo '{build_script}' > {go_test_dir}/build.sh").raise_on_error()
        ssh.run(f"chmod +x {go_test_dir}/build.sh").raise_on_error()
    
    def setup_docker_environment(self, ssh):
        """Set up Docker environment with Conda, Kafka, and Vertica."""
        if not (self.config.MODULE_CONFIG["install_docker"] and 
                (self.config.MODULE_CONFIG["install_conda"] or 
                 self.config.MODULE_CONFIG["install_kafka"] or 
                 self.config.MODULE_CONFIG["install_vertica"])):
            return
        
        print("Setting up Docker environment...")
        
        # Create Dockerfile
        print("  - Creating Dockerfile...")
        dockerfile_content = self.generate_dockerfile()
        base_dir = self.config.DIR_CONFIG["base_dir"]
        ssh.run(f"echo '{dockerfile_content}' > {base_dir}/{self.config.DOCKER_CONFIG['dockerfile']}").raise_on_error()
        
        # Create docker-compose.yml
        print("  - Creating docker-compose.yml...")
        docker_compose_content = self.generate_docker_compose()
        ssh.run(f"echo '{docker_compose_content}' > {base_dir}/{self.config.DOCKER_CONFIG['compose_file']}").raise_on_error()
        
        # Create start.sh
        print("  - Creating start.sh...")
        start_script_content = self.generate_start_script()
        ssh.run(f"echo '{start_script_content}' > {base_dir}/{self.config.DOCKER_CONFIG['start_script']}").raise_on_error()
        ssh.run(f"chmod +x {base_dir}/{self.config.DOCKER_CONFIG['start_script']}").raise_on_error()
        
        # Build Docker environment
        print("  - Building Docker containers (this may take a while)...")
        result = ssh.run(f"cd {base_dir} && docker-compose build")
        if result.exit_code != 0:
            print(f"Warning: Docker build returned non-zero exit code: {result.exit_code}")
            print(f"Output: {str(result)}")
            print(f"Error: {str(result)}")
        
        # Start Docker containers
        print("  - Starting Docker containers...")
        result = ssh.run(f"cd {base_dir} && docker-compose up -d")
        if result.exit_code != 0:
            print(f"Warning: Docker compose up returned non-zero exit code: {result.exit_code}")
            print(f"Output: {str(result)}")
            print(f"Error: {str(result)}")
        
        # Verify containers are running
        print("  - Verifying containers...")
        ssh.run("docker ps").raise_on_error()
    
    def generate_dockerfile(self):
        """Generate Dockerfile content based on configuration."""
        dockerfile = """FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    wget \\
    curl \\
    gnupg2 \\
    software-properties-common \\
    apt-transport-https \\
    ca-certificates \\
    openjdk-11-jdk \\
    python3 \\
    python3-pip \\
    git \\
    unzip \\
    netcat \\
    sudo \\
    && rm -rf /var/lib/apt/lists/*
"""
        
        # Add Conda installation if enabled
        if self.config.MODULE_CONFIG["install_conda"]:
            dockerfile += """
# Install Miniconda
ENV CONDA_DIR /opt/conda
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh && \\
    /bin/bash ~/miniconda.sh -b -p $CONDA_DIR && \\
    rm ~/miniconda.sh

# Add conda to path
ENV PATH=$CONDA_DIR/bin:$PATH

# Create conda environment
RUN conda create -n trading_env python=3.9 -y
SHELL ["/bin/bash", "-c"]
RUN echo "source activate trading_env" >> ~/.bashrc
ENV PATH $CONDA_DIR/envs/trading_env/bin:$PATH

# Install Python packages in the conda environment
RUN conda install -n trading_env -c conda-forge \\
    numpy \\
    pandas \\
    scipy \\
    matplotlib \\
    scikit-learn \\
    jupyterlab \\
    ipykernel \\
    -y
"""
        
        # Add Kafka installation if enabled
        if self.config.MODULE_CONFIG["install_kafka"]:
            dockerfile += """
# Install Kafka
ENV KAFKA_VERSION=3.5.1
ENV SCALA_VERSION=2.13
ENV KAFKA_HOME=/opt/kafka
RUN mkdir -p $KAFKA_HOME && \\
    wget -q https://archive.apache.org/dist/kafka/${KAFKA_VERSION}/kafka_${SCALA_VERSION}-${KAFKA_VERSION}.tgz -O /tmp/kafka.tgz && \\
    tar -xzf /tmp/kafka.tgz -C /opt && \\
    mv /opt/kafka_${SCALA_VERSION}-${KAFKA_VERSION}/* $KAFKA_HOME && \\
    rm -rf /opt/kafka_${SCALA_VERSION}-${KAFKA_VERSION} && \\
    rm /tmp/kafka.tgz

# Add Kafka to PATH
ENV PATH=$PATH:$KAFKA_HOME/bin
"""
        
        # Add Vertica client installation if enabled
        if self.config.MODULE_CONFIG["install_vertica"]:
            dockerfile += """
# Install Vertica client
RUN wget -q https://www.vertica.com/client_drivers/12.0.x/12.0.4-0/vertica-client-12.0.4-0.x86_64.tar.gz -O /tmp/vertica-client.tar.gz && \\
    mkdir -p /opt/vertica && \\
    tar -xzf /tmp/vertica-client.tar.gz -C /opt/vertica && \\
    rm /tmp/vertica-client.tar.gz

# Install Vertica Python client
RUN pip install vertica-python
"""
        
        # Add final parts of Dockerfile
        dockerfile += """
# Create working directory
WORKDIR /app

# Copy startup script
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Expose ports
"""
        
        # Add port exposures
        if self.config.MODULE_CONFIG["install_kafka"]:
            dockerfile += """# Kafka
EXPOSE 9092
# Zookeeper
EXPOSE 2181
"""
        
        if self.config.MODULE_CONFIG["install_jupyter"]:
            dockerfile += """# Jupyter
EXPOSE 8888
"""
        
        # Add entrypoint
        dockerfile += """
# Set entrypoint
ENTRYPOINT ["/app/start.sh"]
"""
        
        return dockerfile
    
    def generate_docker_compose(self):
        """Generate docker-compose.yml content based on configuration."""
        docker_compose = """version: '3'

services:
  trading-environment:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: trading-environment
    ports:
"""
        
        # Add port mappings
        if self.config.MODULE_CONFIG["install_jupyter"]:
            docker_compose += """      # Jupyter Lab
      - "8888:8888"
"""
        
        if self.config.MODULE_CONFIG["install_kafka"]:
            docker_compose += """      # Kafka
      - "9092:9092"
      # Zookeeper
      - "2181:2181"
"""
        
        # Add volume mappings
        docker_compose += """    volumes:
      # Mount your local data directory
      - ./data:/app/data
      # Mount your notebooks directory
      - ./notebooks:/app/notebooks
    environment:
"""
        
        # Add environment variables
        if self.config.MODULE_CONFIG["install_kafka"]:
            docker_compose += """      # Kafka configuration
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
"""
        
        docker_compose += """    restart: unless-stopped
"""
        
        return docker_compose
    
    def generate_start_script(self):
        """Generate start.sh script content based on configuration."""
        start_script = """#!/bin/bash
set -e

"""
        
        # Add Conda activation if enabled
        if self.config.MODULE_CONFIG["install_conda"]:
            start_script += """# Activate conda environment
source /opt/conda/etc/profile.d/conda.sh
conda activate trading_env

"""
        
        # Add Kafka startup if enabled
        if self.config.MODULE_CONFIG["install_kafka"]:
            start_script += """# Start Zookeeper in background
echo "Starting Zookeeper..."
$KAFKA_HOME/bin/zookeeper-server-start.sh $KAFKA_HOME/config/zookeeper.properties &
sleep 10

# Start Kafka in background
echo "Starting Kafka..."
$KAFKA_HOME/bin/kafka-server-start.sh $KAFKA_HOME/config/server.properties &
sleep 10

# Create a default topic
echo "Creating default topic 'trading-data'..."
$KAFKA_HOME/bin/kafka-topics.sh --create --topic trading-data --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1 || true

"""
        
        # Add Jupyter startup if enabled
        if self.config.MODULE_CONFIG["install_jupyter"]:
            start_script += """# Start Jupyter Lab
echo "Starting Jupyter Lab..."
jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root --NotebookApp.token='' --NotebookApp.password=''
"""
        else:
            start_script += """# Keep container running
echo "Container started, keeping it running..."
tail -f /dev/null
"""
        
        return start_script
    
    def create_test_script(self, ssh):
        """Create a test script to verify all environments."""
        print("Creating test script...")
        
        test_script = """#!/bin/bash
echo "=== Morph.so Environment Test Script ==="
echo ""

echo "=== Host Environment ==="
"""
        
        # Add Python/Conda tests if enabled
        if self.config.MODULE_CONFIG["install_conda"]:
            test_script += """echo "Python version:"
python --version
echo "Conda version:"
/opt/conda/bin/conda --version
echo ""
"""
        
        # Add Docker tests if enabled
        if self.config.MODULE_CONFIG["install_docker"]:
            test_script += """echo "=== Docker Environment ==="
echo "Docker version:"
docker --version
echo "Docker Compose version:"
docker-compose --version
echo ""

echo "=== Docker Container Environment ==="
CONTAINER_ID=$(docker ps -q | head -n 1)
if [ -n "$CONTAINER_ID" ]; then
    echo "Container ID: $CONTAINER_ID"
    echo "Python version in container:"
    docker exec $CONTAINER_ID python --version
    echo "Conda version in container:"
    docker exec $CONTAINER_ID conda --version
else
    echo "No running containers found"
fi
echo ""
"""
        
        # Add Kubernetes tests if enabled
        if self.config.MODULE_CONFIG["install_kubernetes"]:
            test_script += """echo "=== Kubernetes Environment ==="
echo "kubectl version:"
kubectl version --client
echo "minikube version:"
minikube version
if [ -x "$(command -v helm)" ]; then
    echo "Helm version:"
    helm version
fi
echo ""
"""
        
        # Add C++ tests if enabled
        if self.config.MODULE_CONFIG["install_cpp"]:
            test_script += """echo "=== C++ Environment ==="
echo "GCC version:"
gcc --version
echo "G++ version:"
g++ --version
echo "CMake version:"
cmake --version
echo ""
"""
        
        # Add Go tests if enabled
        if self.config.MODULE_CONFIG["install_go"]:
            test_script += """echo "=== Go Environment ==="
echo "Go version:"
/usr/local/go/bin/go version
echo ""
"""
        
        # Write test script to file
        base_dir = self.config.DIR_CONFIG["base_dir"]
        ssh.run(f"echo '{test_script}' > {base_dir}/test_environments.sh").raise_on_error()
        ssh.run(f"chmod +x {base_dir}/test_environments.sh").raise_on_error()
        
        # Run the test script
        print("  - Testing all environments...")
        ssh.run(f"{base_dir}/test_environments.sh").raise_on_error()
    
    def expose_services(self):
        """Expose services for external access."""
        print("Exposing services...")
        
        # Expose Jupyter if enabled
        if self.config.SERVICES_CONFIG["expose_jupyter"]:
            print("  - Exposing Jupyter service...")
            self.instance.expose_http_service("jupyter", self.config.SERVICES_CONFIG["jupyter_port"])
            jupyter_url = f"https://jupyter-{self.instance.id.replace('_', '-')}.http.cloud.morph.so"
            print(f"✓ Jupyter available at: {jupyter_url}")
        
        # Expose Kubernetes dashboard if enabled
        if self.config.SERVICES_CONFIG["expose_kubernetes_dashboard"] and self.config.MODULE_CONFIG["install_kubernetes"]:
            print("  - Exposing Kubernetes dashboard...")
            self.instance.expose_http_service("k8s-dashboard", self.config.SERVICES_CONFIG["kubernetes_dashboard_port"])
            k8s_url = f"https://k8s-dashboard-{self.instance.id.replace('_', '-')}.http.cloud.morph.so"
            print(f"✓ Kubernetes dashboard available at: {k8s_url}")
    
    def create_final_snapshot(self):
        """Create a snapshot of the fully configured environment."""
        print("\nCreating snapshot of configured environment...")
        configured_snapshot = self.instance.snapshot()
        print(f"✓ Created configured snapshot: {configured_snapshot.id}")
        return configured_snapshot
    
    def create_readme(self, ssh):
        """Create a README file with usage instructions."""
        print("Creating README file...")
        
        readme = """# Modular Morph.so Environment

This environment has been set up with the following components:

"""
        # Add components based on configuration
        if self.config.MODULE_CONFIG["install_docker"]:
            readme += "- Docker and Docker Compose\n"
        if self.config.MODULE_CONFIG["install_conda"]:
            readme += "- Conda for Python package management\n"
        if self.config.MODULE_CONFIG["install_kafka"]:
            readme += "- Kafka for event streaming\n"
        if self.config.MODULE_CONFIG["install_vertica"]:
            readme += "- Vertica client for database access\n"
        if self.config.MODULE_CONFIG["install_kubernetes"]:
            readme += "- Kubernetes (minikube) for container orchestration\n"
        if self.config.MODULE_CONFIG["install_cpp"]:
            readme += "- C++ development environment\n"
        if self.config.MODULE_CONFIG["install_go"]:
            readme += "- Go programming language\n"
        if self.config.MODULE_CONFIG["install_jupyter"]:
            readme += "- Jupyter Lab for interactive development\n"
        
        readme += f"""
## Directory Structure

```
"""
        # Add directory structure based on configuration
        for dir_name, dir_path in self.config.DIR_CONFIG.items():
            readme += f"{dir_path}/\n"
        
        readme += """```

## Usage Instructions

### Docker Environment

"""
        if self.config.MODULE_CONFIG["install_docker"]:
            readme += f"""To manage Docker containers:
```bash
cd {self.config.DIR_CONFIG["base_dir"]}
docker-compose up -d    # Start containers
docker-compose down     # Stop containers
docker-compose logs     # View container logs
```

"""
        
        # Add Kubernetes instructions if enabled
        if self.config.MODULE_CONFIG["install_kubernetes"]:
            readme += """### Kubernetes Environment

To start minikube:
```bash
minikube start --driver=docker
```

To access the Kubernetes dashboard:
```bash
minikube dashboard
```

"""
        
        # Add C++ instructions if enabled
        if self.config.MODULE_CONFIG["install_cpp"]:
            readme += f"""### C++ Development

A sample C++ project is available at {self.config.DIR_CONFIG["cpp_dir"]}/projects/hello_world

To build and run:
```bash
cd {self.config.DIR_CONFIG["cpp_dir"]}/projects/hello_world
./build.sh
./build/hello_world
```

"""
        
        # Add Go instructions if enabled
        if self.config.MODULE_CONFIG["install_go"]:
            readme += f"""### Go Development

A sample Go project is available at {self.config.DIR_CONFIG["go_dir"]}/projects/hello_world

To build and run:
```bash
cd {self.config.DIR_CONFIG["go_dir"]}/projects/hello_world
./build.sh
./hello_world
```

"""
        
        # Add testing instructions
        readme += f"""### Testing All Environments

To verify all installed components:
```bash
{self.config.DIR_CONFIG["base_dir"]}/test_environments.sh
```

"""
        
        # Write README to file
        base_dir = self.config.DIR_CONFIG["base_dir"]
        ssh.run(f"echo '{readme}' > {base_dir}/README.md").raise_on_error()
    
    def run(self):
        """Run the setup process."""
        # Create VM
        self.create_vm()
        
        # Set up environment
        with self.instance.ssh() as ssh:
            # Set up directory structure
            self.setup_directories(ssh)
            
            # Install host tools
            self.install_host_tools(ssh)
            
            # Install Docker
            self.install_docker(ssh)
            
            # Install Kubernetes
            self.install_kubernetes(ssh)
            
            # Install C++
            self.install_cpp(ssh)
            
            # Install Go
            self.install_go(ssh)
            
            # Set up Docker environment
            self.setup_docker_environment(ssh)
            
            # Create test script
            self.create_test_script(ssh)
            
            # Create README
            self.create_readme(ssh)
        
        # Expose services
        self.expose_services()
        
        # Create final snapshot
        configured_snapshot = self.create_final_snapshot()
        
        # Print summary
        print("\n=== Environment Setup Complete ===")
        print(f"Instance ID: {self.instance.id}")
        print(f"Snapshot ID: {configured_snapshot.id}")
        
        # Print service URLs
        if self.config.SERVICES_CONFIG["expose_jupyter"]:
            print(f"Jupyter URL: https://jupyter-{self.instance.id.replace('_', '-')}.http.cloud.morph.so")
        
        if self.config.SERVICES_CONFIG["expose_kubernetes_dashboard"] and self.config.MODULE_CONFIG["install_kubernetes"]:
            print(f"Kubernetes Dashboard URL: https://k8s-dashboard-{self.instance.id.replace('_', '-')}.http.cloud.morph.so")
        
        print("\nTo start a new instance from this snapshot:")
        print(f"  new_instance = client.instances.start('{configured_snapshot.id}')")
        
        if self.config.SERVICES_CONFIG["expose_jupyter"]:
            print("  new_instance.expose_http_service('jupyter', 8888)")
            print("  print(f\"Jupyter URL: https://jupyter-{new_instance.id.replace('_', '-')}.http.cloud.morph.so\")")
        
        # Return the configured snapshot ID
        return configured_snapshot.id

def main():
    """Main entry point."""
    args = parse_args()
    config = load_config(args.config)
    
    setup = MorphSetup(config)
    setup.run()

if __name__ == "__main__":
    main()
