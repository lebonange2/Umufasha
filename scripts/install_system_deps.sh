#!/bin/bash
# Install system dependencies for the brainstorming assistant

set -e

echo "🔧 Installing System Dependencies"
echo "=================================="
echo ""

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo "Cannot detect OS"
    exit 1
fi

echo "Detected OS: $OS"
echo ""

# Install based on OS
case $OS in
    ubuntu|debian|pop)
        echo "Installing for Ubuntu/Debian..."
        sudo apt-get update
        sudo apt-get install -y \
            portaudio19-dev \
            python3-pyaudio \
            libasound2-dev \
            python3-dev \
            build-essential
        ;;
    
    fedora|rhel|centos)
        echo "Installing for Fedora/RHEL/CentOS..."
        sudo dnf install -y \
            portaudio-devel \
            alsa-lib-devel \
            python3-devel \
            gcc
        ;;
    
    arch|manjaro)
        echo "Installing for Arch Linux..."
        sudo pacman -S --noconfirm \
            portaudio \
            alsa-lib \
            python \
            base-devel
        ;;
    
    *)
        echo "Unsupported OS: $OS"
        echo ""
        echo "Please install PortAudio manually:"
        echo "  Ubuntu/Debian: sudo apt-get install portaudio19-dev"
        echo "  Fedora/RHEL:   sudo dnf install portaudio-devel"
        echo "  Arch:          sudo pacman -S portaudio"
        exit 1
        ;;
esac

echo ""
echo "✅ System dependencies installed!"
echo ""
echo "Next steps:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Reinstall Python packages: pip install --force-reinstall sounddevice"
echo "  3. Test audio: python3 scripts/check_audio.py"
echo "  4. Run app: python3 app.py"
