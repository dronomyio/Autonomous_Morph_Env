#!/usr/bin/env python3
"""
Configuration file for Morph.so modular setup script.
Contains all configurable parameters for the setup process.
"""

# VM Configuration
VM_CONFIG = {
    "image_id": "morphvm-minimal",
    "vcpus": 4,
    "memory": 8192,  # 8GB
    "disk_size": 50000,  # 50GB
    "username": "root",  # Default username on the VM
}

# Directory Configuration
DIR_CONFIG = {
    "base_dir": "/root/trading_env",  # Using root as default user
    "data_dir": "/root/trading_env/data",
    "notebooks_dir": "/root/trading_env/notebooks",
    "kubernetes_dir": "/root/trading_env/kubernetes",
    "cpp_dir": "/root/trading_env/cpp",
    "go_dir": "/root/trading_env/go",
    "nats_dir": "/root/trading_env/nats",  # Added NATS directory
}

# Module Configuration
MODULE_CONFIG = {
    "install_docker": True,
    "install_conda": True,
    "install_kafka": True,
    "install_vertica": True,
    "install_kubernetes": True,
    "install_cpp": True,
    "install_go": True,
    "install_jupyter": True,
    "install_nats": True,  # Added NATS installation flag
}

# Docker Configuration
DOCKER_CONFIG = {
    "compose_file": "docker-compose.yml",
    "dockerfile": "Dockerfile",
    "start_script": "start.sh",
}

# Kubernetes Configuration
KUBERNETES_CONFIG = {
    "version": "1.27.0",
    "install_minikube": True,
    "install_kubectl": True,
    "install_helm": True,
}

# Programming Languages Configuration
LANGUAGES_CONFIG = {
    "cpp": {
        "install_gcc": True,
        "install_cmake": True,
        "gcc_version": "11",
    },
    "go": {
        "version": "1.20.3",
    },
}

# NATS Configuration
NATS_CONFIG = {
    "version": "2.9.17",  # Latest stable version
    "client_port": 4222,
    "http_port": 8222,
    "routing_port": 6222,
    "install_nats_py": True,  # Install Python client for NATS
    "cluster_name": "trading_cluster",
    "jetstream_enabled": True,  # Enable JetStream for persistent messaging
}

# Service Exposure Configuration
SERVICES_CONFIG = {
    "expose_jupyter": True,
    "jupyter_port": 8888,
    "expose_kubernetes_dashboard": True,
    "kubernetes_dashboard_port": 8001,
    "expose_nats_monitoring": True,  # Added NATS monitoring exposure
    "nats_monitoring_port": 8222,
}
