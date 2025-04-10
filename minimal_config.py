#!/usr/bin/env python3
"""
Minimal configuration file for Morph.so setup script.
Contains only essential components for faster installation.
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
    "nats_dir": "/root/trading_env/nats",  # Added NATS directory
}

# Module Configuration - Only essential components enabled
MODULE_CONFIG = {
    "install_docker": True,
    "install_conda": True,
    "install_kafka": True,
    "install_vertica": True,
    "install_kubernetes": False,  # Disabled for faster installation
    "install_cpp": False,         # Disabled for faster installation
    "install_go": False,          # Disabled for faster installation
    "install_jupyter": True,
    "install_nats": True,         # Added NATS installation flag
}

# Docker Configuration
DOCKER_CONFIG = {
    "compose_file": "docker-compose.yml",
    "dockerfile": "Dockerfile",
    "start_script": "start.sh",
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
    "expose_kubernetes_dashboard": False,
    "kubernetes_dashboard_port": 8001,
    "expose_nats_monitoring": True,  # Added NATS monitoring exposure
    "nats_monitoring_port": 8222,
}
