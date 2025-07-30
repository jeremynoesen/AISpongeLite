#! /bin/bash

# Check if the script is run as root
if [ "$(id -u)" -ne 0 ]; then
    echo "This script must be run as root. Please use sudo."
    exit 1
fi

# Pre-installation messages
echo "This script will install AI Sponge Lite on your system."
echo "This script will also install Git and Docker if they are not already installed."

# Prompt user tokens
read -p "Enter your Discord bot token: " DISCORD_BOT_TOKEN
read -p "Enter your OpenAI API key: " OPENAI_API_KEY

# Install Git if not already installed
if ! command -v git &> /dev/null; then

    # Debian/Ubuntu
    if [ -f /etc/debian_version ]; then
        apt update
        apt install git -y

    # Red Hat/CentOS/Fedora
    elif [ -f /etc/redhat-release ]; then
        dnf update
        dnf install git -y

    else
        echo "Unsupported distribution. Please install Git manually."
        exit 1

    fi

fi

# Install Docker if not already installed
if ! command -v docker &> /dev/null; then
    curl -sSL https://get.docker.com | sh
fi

# Clone the repository
git clone https://github.com/jeremynoesen/AISpongeLite.git
cd AISpongeLite

# Create .env file
echo "DISCORD_BOT_TOKEN=$DISCORD_BOT_TOKEN" >> .env
echo "OPENAI_API_KEY=$OPENAI_API_KEY" >> .env

# Build the Docker image and start the container
docker compose up -d

# Installation is complete
echo "AI Sponge Lite has been installed on your system and is now running."