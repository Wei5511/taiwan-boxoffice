#!/bin/bash

# --- CONFIGURATION ---
PROJECT_DIR="/home/$(whoami)/taiwan-boxoffice-scraper"
VENV_DIR="$PROJECT_DIR/venv"
PORT=8000

echo "🚀 Starting Deployment for Taiwan Box Office Backend..."

# 1. System Dependencies
echo "📦 Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip sqlite3 nginx git

# 2. Setup Venv & Install Requirements
echo "🐍 Setting up Python environment..."
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    # Fallback if requirements.txt is missing
    pip install fastapi uvicorn sqlmodel sqlalchemy apscheduler playwright pandas openpyxl gunicorn
fi

# 3. Setup Playwright
echo "🎭 Installing Playwright browsers..."
playwright install chromium
playwright install-deps

# 4. Create Systemd Service
echo "⚙️ Creating Systemd service..."
sudo tee /etc/systemd/system/boxoffice-backend.service > /dev/null <<EOF
[Unit]
Description=Gunicorn instance to serve Taiwan Box Office API
After=network.target

[Service]
User=$(whoami)
Group=www-data
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$VENV_DIR/bin"
Environment="ALLOWED_ORIGINS=*"
ExecStart=$VENV_DIR/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:$PORT

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable boxoffice-backend
sudo systemctl restart boxoffice-backend

echo "✅ Backend is running on port $PORT"
echo "👉 You can check status with: sudo systemctl status boxoffice-backend"
echo ""
echo "🔗 Next step: Configure Nginx to proxy /api to http://localhost:$PORT"
