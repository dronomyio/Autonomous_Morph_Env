#!/bin/bash
# fix_docker_compose.sh - Comprehensive fix for Docker Compose version issue

# Define colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting Docker Compose fix script...${NC}"

# 1. Fix the docker-compose.yml file if it exists
if [ -f "/root/trading_env/docker-compose.yml" ]; then
    echo "Found existing docker-compose.yml, fixing version format..."
    sed -i 's/version: 3/version: "3"/' /root/trading_env/docker-compose.yml
    echo -e "${GREEN}✓ Fixed version format in existing docker-compose.yml${NC}"
    
    # Try to build and run with the fixed file
    echo "Attempting to build and run containers with fixed configuration..."
    cd /root/trading_env
    docker-compose build
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Docker build successful${NC}"
        docker-compose up -d
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Containers started successfully${NC}"
        else
            echo -e "${YELLOW}Warning: Container startup had issues${NC}"
        fi
    else
        echo -e "${YELLOW}Warning: Docker build had issues${NC}"
    fi
fi

# 2. Fix the setup.py file to prevent future issues
echo "Fixing setup.py to prevent future version format issues..."
if [ -f "/root/morph_modular_setup/setup.py" ]; then
    # Use sed to replace version: 3 with version: "3" in the setup.py file
    sed -i 's/"version": 3/"version": "3"/g' /root/morph_modular_setup/setup.py
    echo -e "${GREEN}✓ Fixed version format in setup.py${NC}"
else
    echo -e "${YELLOW}Warning: Could not find setup.py in expected location${NC}"
fi

echo -e "${GREEN}Fix script completed!${NC}"
echo "You can now run ./run_setup.sh --config minimal_config.py again if needed"

