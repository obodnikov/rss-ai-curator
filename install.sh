#!/bin/bash

# RSS AI Curator - Installation Script
# This script helps you set up the project quickly

set -e  # Exit on error

echo "=================================================="
echo "  RSS AI Curator - Installation Script"
echo "=================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo -e "${RED}Error: Python 3.9+ required. You have Python $python_version${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python $python_version found${NC}"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment already exists, skipping...${NC}"
else
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install --upgrade pip > /dev/null
pip install -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Create directories
echo ""
echo "Creating directories..."
mkdir -p data logs config
touch data/.gitkeep logs/.gitkeep
echo -e "${GREEN}✓ Directories created${NC}"

# Copy config files if they don't exist
echo ""
echo "Setting up configuration files..."

if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✓ .env file created from template${NC}"
        echo -e "${YELLOW}  ⚠ Please edit .env and add your API keys${NC}"
    else
        echo -e "${YELLOW}  ⚠ .env.example not found, creating blank .env${NC}"
        cat > .env << 'EOF'
# OpenAI API Key (Required)
OPENAI_API_KEY=your-openai-key-here

# Anthropic API Key (Optional)
ANTHROPIC_API_KEY=your-anthropic-key-here

# Telegram Configuration (Required)
TELEGRAM_BOT_TOKEN=your-bot-token-here
TELEGRAM_ADMIN_USER_ID=your-telegram-user-id
EOF
        echo -e "${GREEN}✓ .env file created${NC}"
    fi
else
    echo -e "${YELLOW}  .env file already exists, skipping...${NC}"
fi

# Initialize database with shown_to_user fields
echo ""
echo "Initializing database with shown tracking..."
python main.py init
echo -e "${GREEN}✓ Database initialized with shown_to_user fields${NC}"

# Print next steps
echo ""
echo "=================================================="
echo -e "${GREEN}  Installation Complete! 🎉${NC}"
echo "=================================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Edit .env file with your API keys:"
echo "   nano .env"
echo ""
echo "2. Customize your RSS feeds in config/config.yaml"
echo ""
echo "3. Start the bot:"
echo "   python main.py start"
echo ""
echo "4. Or run individual commands:"
echo "   python main.py fetch   # Fetch RSS feeds"
echo "   python main.py digest  # Generate digest"
echo "   python main.py stats   # Show statistics"
echo ""
echo "For detailed documentation, see:"
echo "  - README.md"
echo "  - docs/SETUP_GUIDE.md"
echo ""
echo "ℹ️  Note: Articles are tracked with 'shown_to_user' field"
echo "   No migration needed - database created with v0.1.0 schema!"
echo ""
echo "=================================================="
