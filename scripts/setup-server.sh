#!/bin/bash
# Server setup script for Telegram Bot
# Run: curl -sSL https://raw.githubusercontent.com/vietdqjv/tool-auto-task-telegram/main/scripts/setup-server.sh | bash

set -e

APP_DIR="/opt/telegram-bot"
COMPOSE_VERSION="v2.24.0"

echo "=== Telegram Bot Server Setup ==="

# Check root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root: sudo bash setup-server.sh"
  exit 1
fi

# Update system
echo "[1/6] Updating system..."
apt-get update && apt-get upgrade -y

# Install Docker
echo "[2/6] Installing Docker..."
if ! command -v docker &> /dev/null; then
  curl -fsSL https://get.docker.com | sh
  systemctl enable docker
  systemctl start docker
fi

# Install Docker Compose
echo "[3/6] Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
  curl -SL "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-linux-x86_64" \
    -o /usr/local/bin/docker-compose
  chmod +x /usr/local/bin/docker-compose
fi

# Create app directory
echo "[4/6] Creating app directory..."
mkdir -p $APP_DIR
cd $APP_DIR

# Download docker-compose.yml
echo "[5/6] Downloading docker-compose.yml..."
curl -sSL https://raw.githubusercontent.com/vietdqjv/tool-auto-task-telegram/main/docker/docker-compose.yml \
  -o docker-compose.yml

# Create .env file
echo "[6/6] Creating .env file..."
if [ ! -f .env ]; then
  cat > .env << 'EOF'
# Telegram Bot Token from @BotFather
BOT_TOKEN=your_bot_token_here

# Admin user IDs (JSON array)
ADMIN_IDS=[123456789]

# Database password
DB_PASSWORD=change_this_secure_password

# Redis
REDIS_URL=redis://redis:6379/0

# Database
DATABASE_URL=postgresql+asyncpg://bot:${DB_PASSWORD}@db:5432/telegram_bot
EOF
  echo "Created .env file. Please edit with your values!"
else
  echo ".env already exists, skipping..."
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Edit .env file: nano $APP_DIR/.env"
echo "2. Add your BOT_TOKEN from @BotFather"
echo "3. Change DB_PASSWORD to something secure"
echo "4. Start services: docker-compose up -d"
echo "5. View logs: docker-compose logs -f bot"
echo ""
echo "For auto-deploy from GitHub, add these secrets:"
echo "  - SSH_PRIVATE_KEY: Your SSH private key"
echo "  - SERVER_HOST: $(curl -s ifconfig.me)"
echo "  - SERVER_USER: root"
echo "  - APP_DIR: $APP_DIR"
