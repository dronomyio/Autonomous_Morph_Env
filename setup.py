#!/usr/bin/env python3
"""
Modular setup script for Morph.so environments.

This script creates a customizable Morph.so environment with support for:
- Docker and Docker Compose
- Conda for Python package management
- Kafka for event streaming
- Vertica client for database access
- NATS.io messaging system
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
    
    def install_nats(self, ssh):
        """Install NATS.io on the VM."""
        if not self.config.MODULE_CONFIG["install_nats"]:
            return
        
        print("Installing NATS.io...")
        nats_version = self.config.NATS_CONFIG["version"]
        
        # Create NATS directory
        nats_dir = self.config.DIR_CONFIG["nats_dir"]
        ssh.run(f"mkdir -p {nats_dir}/config").raise_on_error()
        
        # Download and install NATS server
        print(f"  - Installing NATS server {nats_version}...")
        ssh.run(f"curl -L https://github.com/nats-io/nats-server/releases/download/v{nats_version}/nats-server-v{nats_version}-linux-amd64.tar.gz -o /tmp/nats-server.tar.gz").raise_on_error()
        ssh.run("tar -xzf /tmp/nats-server.tar.gz -C /tmp").raise_on_error()
        ssh.run(f"mv /tmp/nats-server-v{nats_version}-linux-amd64/nats-server /usr/local/bin/").raise_on_error()
        ssh.run("rm -rf /tmp/nats-server*").raise_on_error()
        
        # Verify NATS server installation
        ssh.run("nats-server --version").raise_on_error()
        
        # Install NATS CLI
        print("  - Installing NATS CLI...")
        ssh.run("curl -L https://github.com/nats-io/natscli/releases/latest/download/nats-$(uname -s)-$(uname -m).zip -o /tmp/nats-cli.zip").raise_on_error()
        ssh.run("apt-get install -y unzip").raise_on_error()
        ssh.run("unzip -o /tmp/nats-cli.zip -d /tmp").raise_on_error()
        ssh.run("mv /tmp/nats /usr/local/bin/").raise_on_error()
        ssh.run("rm /tmp/nats-cli.zip").raise_on_error()
        
        # Verify NATS CLI installation
        ssh.run("nats --version").raise_on_error()
        
        # Install NATS Python client if enabled
        if self.config.NATS_CONFIG["install_nats_py"]:
            
(Content truncated due to size limit. Use line ranges to read in chunks)