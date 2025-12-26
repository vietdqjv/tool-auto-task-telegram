#!/bin/bash
# Server setup script for Telegram Bot
# Run: curl -sSL https://raw.githubusercontent.com/vietdqjv/tool-auto-task-telegram/main/scripts/setup-server.sh | bash

set -e

APP_DIR="/opt/telegram-bot"
REPO_URL="https://raw.githubusercontent.com/vietdqjv/tool-auto-task-telegram/main"

echo "=== Telegram Bot Server Setup ==="

# Check root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root: sudo bash setup-server.sh"
  exit 1
fi

# Detect architecture
ARCH=$(uname -m)
case $ARCH in
  x86_64) ARCH="amd64" ;;
  aarch64|arm64) ARCH="arm64" ;;
  *) echo "Unsupported architecture: $ARCH"; exit 1 ;;
esac
echo "Detected architecture: $ARCH"

# Update system
echo "[1/5] Updating system..."
apt-get update && apt-get upgrade -y

# Install Docker (includes Compose plugin)
echo "[2/5] Installing Docker..."
if ! command -v docker &> /dev/null; then
  curl -fsSL https://get.docker.com | sh
  systemctl enable docker
  systemctl start docker
else
  echo "Docker already installed: $(docker --version)"
fi

# Verify Docker Compose plugin
echo "[3/5] Verifying Docker Compose..."
if docker compose version &> /dev/null; then
  echo "Docker Compose plugin: $(docker compose version)"
else
  echo "Installing Docker Compose plugin..."
  apt-get install -y docker-compose-plugin
fi

# Create app directory and logs
echo "[4/5] Creating app directories..."
mkdir -p $APP_DIR/logs
cd $APP_DIR

# Download docker-compose.yml and Dockerfile
echo "[5/5] Downloading configuration files..."
curl -sSL "$REPO_URL/docker/docker-compose.yml" -o docker-compose.yml
curl -sSL "$REPO_URL/docker/Dockerfile" -o Dockerfile

# Create .env file
if [ ! -f .env ]; then
  cat > .env << 'EOF'
# Telegram Bot Token from @BotFather
BOT_TOKEN=your_bot_token_here

# Admin user IDs (JSON array)
ADMIN_IDS=[123456789]

# Database password (CHANGE THIS!)
DB_PASSWORD=change_this_secure_password

# Redis (for FSM storage)
REDIS_URL=redis://redis:6379/0

# Database (auto-configured for docker)
DATABASE_URL=postgresql+asyncpg://bot:${DB_PASSWORD}@db:5432/telegram_bot

# Scheduler jobstore (optional, defaults to DATABASE_URL)
SCHEDULER_JOBSTORE_URL=

# Rate Limiting
RATE_LIMIT_REQUESTS=5
RATE_LIMIT_PERIOD=60

# Working Hours (optional)
# TIMEZONE=Asia/Ho_Chi_Minh
# WORKING_PERIODS=08:00-12:00,13:30-17:30
# WORKING_DAYS=1,2,3,4,5
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
echo "4. Start services: docker compose up -d --build"
echo "5. View logs: docker compose logs -f bot"
echo ""
echo "Useful commands:"
echo "  docker compose ps          # Check status"
echo "  docker compose restart bot # Restart bot"
echo "  docker compose down        # Stop all"
echo ""
echo "For auto-deploy from GitHub, add these secrets:"
echo "  - SSH_PRIVATE_KEY: Your SSH private key"
echo "  - SERVER_HOST: $(curl -s ifconfig.me 2>/dev/null || echo '<your-server-ip>')"
echo "  - SERVER_USER: root"
echo "  - APP_DIR: $APP_DIR"
