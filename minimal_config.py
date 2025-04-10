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
}

# Docker Configuration
DOCKER_CONFIG = {
    "compose_file": "docker-compose.yml",
    "dockerfile": "Dockerfile",
    "start_script": "start.sh",
}

# Service Exposure Configuration
SERVICES_CONFIG = {
    "expose_jupyter": True,
    "jupyter_port": 8888,
    "expose_kubernetes_dashboard": False,
    "kubernetes_dashboard_port": 8001,
}
