#!/bin/bash
# =============================================================================
# BWP Raspberry Pi Zero W Setup Script
# =============================================================================
# This script prepares a Raspberry Pi Zero W for BWP (Bing Wallpaper) with
# Frame TV integration, including USB mass storage emulation support.
#
# Compatible with: Raspberry Pi Zero W (all versions)
# OS: Raspberry Pi OS Lite (32-bit) recommended
# =============================================================================

set -e  # Exit on error
set -u  # Exit on undefined variable

# ANSI color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_NAME="BWP Pi Zero Setup"
BWP_DIR=""  # Will be set to current directory
LOG_FILE="/tmp/bwp_setup.log"

# =============================================================================
# Helper Functions
# =============================================================================

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR] $1${NC}" | tee -a "$LOG_FILE"
}

log_info() {
    echo -e "${BLUE}[INFO] $1${NC}" | tee -a "$LOG_FILE"
}

log_step() {
    echo -e "${PURPLE}[STEP] $1${NC}" | tee -a "$LOG_FILE"
}

check_pi_zero() {
    local hardware
    local model
    hardware=$(grep "^Hardware" /proc/cpuinfo | cut -d: -f2 | xargs)
    model=$(grep "^Model" /proc/cpuinfo | cut -d: -f2 | xargs)

    log_info "Detected hardware: $hardware"
    log_info "Detected model: $model"

    if [[ ! "$model" =~ "Pi Zero" ]]; then
        log_warning "This script is optimized for Pi Zero W. Detected: $model"
        log_warning "Continuing anyway, but performance may vary."
    fi
}

check_internet() {
    log_step "Checking internet connectivity..."
    if ! ping -c 1 8.8.8.8 >/dev/null 2>&1; then
        log_error "No internet connection. Please check WiFi configuration."
        exit 1
    fi
    log "Internet connectivity confirmed"
}

check_storage() {
    local available
    local available_gb
    available=$(df / | awk 'NR==2 {print $4}')
    available_gb=$((available / 1024 / 1024))

    log_info "Available storage: ${available_gb}GB"

    if [ "${available_gb:-0}" -lt 2 ]; then
        log_error "Insufficient storage space. Need at least 2GB free."
        exit 1
    fi
}

# =============================================================================
# System Preparation
# =============================================================================

update_system() {
    log_step "Updating system packages..."
    sudo apt update -y
    sudo apt upgrade -y
    log "System updated successfully"
}

install_build_dependencies() {
    log_step "Installing build dependencies for Python packages..."

    # Essential build tools
    sudo apt install -y \
        build-essential \
        git \
        curl \
        wget \
        vim \
        cron \
        python3-dev

    # Pillow (PIL) dependencies for image processing
    sudo apt install -y \
        libjpeg-dev \
        zlib1g-dev \
        libfreetype6-dev \
        libwebp-dev

    # Optional: Install system Pillow for faster setup
    # sudo apt install -y python3-pil

    log "Build dependencies installed successfully"
}

optimize_memory() {
    log_step "Optimizing memory settings for Pi Zero W..."

    # Temporarily increase swap for package compilation
    local current_swap
    current_swap=$(grep CONF_SWAPSIZE /etc/dphys-swapfile | cut -d= -f2)
    log_info "Current swap size: ${current_swap}MB"

    if [ "${current_swap:-0}" -lt 1024 ]; then
        log "Increasing swap to 1024MB for compilation..."
        sudo dphys-swapfile swapoff
        sudo cp /etc/dphys-swapfile /etc/dphys-swapfile.bwp_backup
        sudo sed -i 's/^CONF_SWAPSIZE=.*/CONF_SWAPSIZE=1024/' /etc/dphys-swapfile
        sudo dphys-swapfile setup
        sudo dphys-swapfile swapon
        log "Swap increased to 1024MB"
    fi

    # GPU memory split optimization for headless operation
    if ! grep -q "gpu_mem=16" /boot/config.txt; then
        log "Optimizing GPU memory for headless operation..."
        echo "gpu_mem=16" | sudo tee -a /boot/config.txt > /dev/null
        log "GPU memory set to 16MB (requires reboot to take effect)"
    fi
}

# =============================================================================
# USB Mass Storage Setup (for Frame TV)
# =============================================================================

setup_usb_gadget_configfs() {
    local disk_image="$1"
    log_step "Setting up USB gadget using configfs..."

    # Create USB gadget configuration script
    local gadget_script="/usr/local/bin/setup_ftv_gadget.sh"
    sudo tee "$gadget_script" > /dev/null << 'EOF'
#!/bin/bash
# USB Gadget setup script for Frame TV

GADGET_DIR="/sys/kernel/config/usb_gadget/ftv_gadget"
DISK_IMAGE="$1"

# Check if gadget already exists
if [ -d "$GADGET_DIR" ]; then
    echo "USB gadget already configured"
    exit 0
fi

# Create the gadget directory
mkdir -p "$GADGET_DIR"
cd "$GADGET_DIR"

# Configure USB device descriptor
echo 0x1d6b > idVendor    # Linux Foundation
echo 0x0104 > idProduct   # Multifunction Composite Gadget
echo 0x0100 > bcdDevice   # v1.0.0
echo 0x0200 > bcdUSB      # USB2

# Configure device strings
mkdir -p strings/0x409
echo "Raspberry Pi Foundation" > strings/0x409/manufacturer
echo "Frame TV USB Storage" > strings/0x409/product
echo "$(cat /proc/cpuinfo | grep Serial | cut -d ' ' -f 2)" > strings/0x409/serialnumber

# Create configuration
mkdir -p configs/c.1/strings/0x409
echo "Config 1: Mass Storage" > configs/c.1/strings/0x409/configuration
echo 250 > configs/c.1/MaxPower

# Create mass storage function
mkdir -p functions/mass_storage.usb0
echo 1 > functions/mass_storage.usb0/stall
echo 0 > functions/mass_storage.usb0/lun.0/cdrom
echo 0 > functions/mass_storage.usb0/lun.0/ro
echo 1 > functions/mass_storage.usb0/lun.0/removable
echo "$DISK_IMAGE" > functions/mass_storage.usb0/lun.0/file

# Link function to configuration
ln -s functions/mass_storage.usb0 configs/c.1/

# Enable gadget
UDC=$(ls /sys/class/udc | head -1)
echo "$UDC" > UDC

echo "USB gadget configured successfully"
EOF

    sudo chmod +x "$gadget_script"
    log "Created USB gadget setup script: $gadget_script"

    # Create systemd service for USB gadget
    local service_file="/etc/systemd/system/ftv-usb-gadget.service"
    sudo tee "$service_file" > /dev/null << EOF
[Unit]
Description=Frame TV USB Gadget Setup
After=network.target
Wants=network.target

[Service]
Type=oneshot
ExecStart=$gadget_script $disk_image
RemainAfterExit=yes
User=root

[Install]
WantedBy=multi-user.target
EOF

    # Enable the service
    sudo systemctl daemon-reload
    sudo systemctl enable ftv-usb-gadget.service
    log "Created and enabled USB gadget systemd service"
}

setup_usb_gadget() {
    log_step "Setting up USB mass storage gadget for Frame TV..."

    # Enable dwc2 overlay for USB gadget mode
    if ! grep -q "^dtoverlay=dwc2" /boot/config.txt; then
        log "Enabling USB gadget mode..."
        echo "dtoverlay=dwc2,dr_mode=otg" | sudo tee -a /boot/config.txt > /dev/null
    elif grep -q "^dtoverlay=dwc2,dr_mode=host" /boot/config.txt; then
        log "Fixing dwc2 mode from host to otg..."
        sudo sed -i 's/^dtoverlay=dwc2,dr_mode=host/dtoverlay=dwc2,dr_mode=otg/' /boot/config.txt
    fi

    # Configure g_mass_storage module with disk image parameter
    local disk_image="$HOME/ftv_images/ftv_disk.img"
    local g_mass_storage_line="g_mass_storage file=$disk_image removable=1 ro=0 stall=0"
    
    # Remove any existing g_mass_storage entries
    sudo sed -i '/g_mass_storage/d' /etc/modules
    
    # Add new g_mass_storage configuration
    echo "$g_mass_storage_line" | sudo tee -a /etc/modules > /dev/null
    log "USB mass storage module configured with disk image"

    # Create image directory for Frame TV
    local ftv_images_dir="$HOME/ftv_images"
    if [ ! -d "$ftv_images_dir" ]; then
        mkdir -p "$ftv_images_dir"
        log "Created Frame TV images directory: $ftv_images_dir"
    fi

    # Create a disk image file for USB mass storage (1GB)
    local disk_image="$ftv_images_dir/ftv_disk.img"
    if [ ! -f "$disk_image" ]; then
        log "Creating 1GB disk image for Frame TV USB storage..."
        dd if=/dev/zero of="$disk_image" bs=1M count=1024 status=progress

        # Format as FAT32
        sudo mkfs.vfat "$disk_image"
        log "Created and formatted disk image: $disk_image"
    fi

    # Set up USB gadget using configfs (modern approach)
    setup_usb_gadget_configfs "$disk_image"
    
    # Install USB helper script
    local usb_helper_script="$BWP_DIR/scripts/usb_helper.sh"
    if [ -f "$usb_helper_script" ]; then
        sudo cp "$usb_helper_script" /usr/local/bin/
        sudo chmod +x /usr/local/bin/usb_helper.sh
        log "Installed USB helper script to /usr/local/bin/"
        
        # Configure sudo permissions for USB helper script
        local sudoers_file="/etc/sudoers.d/bwp-usb-helper"
        echo "$USER ALL=(root) NOPASSWD: /usr/local/bin/usb_helper.sh" | sudo tee "$sudoers_file" > /dev/null
        sudo chmod 440 "$sudoers_file"
        log "Configured sudo permissions for USB helper script"
    else
        log_warning "USB helper script not found: $usb_helper_script"
    fi
    
    # Add user to required groups for USB operations
    if ! groups "$USER" | grep -q disk; then
        sudo usermod -a -G disk "$USER"
        log "Added user to disk group for USB operations"
    fi
    
    log "USB mass storage setup completed"
    log_warning "Reboot required for USB gadget changes to take effect"
}

# =============================================================================
# UV Package Manager Installation
# =============================================================================

install_uv() {
    log_step "Installing UV package manager..."

    if command -v uv >/dev/null 2>&1; then
        log "UV already installed: $(uv --version)"
        return 0
    fi

    # Install UV using the official installer
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # Add UV to PATH for current session
    # shellcheck source=/dev/null
    source "$HOME/.bashrc"

    # Verify installation
    if command -v uv >/dev/null 2>&1; then
        log "UV installed successfully: $(uv --version)"
    else
        log_error "UV installation failed"
        exit 1
    fi
}

# =============================================================================
# BWP Application Setup
# =============================================================================

setup_bwp_directory() {
    log_step "Setting up BWP directory..."

    # Verify we're in the BWP repository directory
    if [ ! -f "setup_pi_zero.sh" ] || [ ! -d "src/abk_bwp" ]; then
        log_error "This script must be run from the BWP repository directory"
        log_error "Please run: cd abk_bwp && ./setup_pi_zero.sh"
        exit 1
    fi

    # Use current directory as BWP directory
    BWP_DIR="$(pwd)"
    log "Using BWP directory: $BWP_DIR"

    # Update repository to latest
    log "Pulling latest changes from repository..."
    git pull

    log "BWP repository ready at: $BWP_DIR"
}

install_bwp_dependencies() {
    log_step "Installing BWP dependencies..."

    # Install BWP in USB mode (optimal for Raspberry Pi Zero W)
    echo
    log_info "Installing BWP in USB mode (optimal for Raspberry Pi Zero W)..."
    log_info "USB mode provides:"
    echo "  • Lower memory usage"
    echo "  • Faster performance on Pi Zero W"
    echo "  • No network dependency for Frame TV connection"
    echo "  • Direct USB mass storage emulation"
    echo

    log "Installing BWP dependencies (USB mode)..."
    uv sync

    log "BWP dependencies installed successfully"
}

configure_bwp() {
    log_step "Configuring BWP for Pi Zero W USB mode..."

    local config_file="src/abk_bwp/config/bwp_config.toml"
    if [ -f "$config_file" ]; then
        # Create a backup of original configuration
        cp "$config_file" "${config_file}.backup"
        log "Created backup: ${config_file}.backup"

        # Configure BWP for USB mass storage mode using Makefile rules
        log "Configuring BWP for USB mass storage mode..."
        
        # Enable auto image fetch (automatic daily downloads)
        make img_auto_fetch_enable
        log "  • Enabled automatic image fetch"
        
        # Disable desktop image setting (not applicable on headless Pi)
        make desktop_disable
        log "  • Disabled desktop wallpaper setting (headless Pi)"
        
        # Enable Frame TV support
        make ftv_enable
        log "  • Enabled Frame TV support"
        
        # Ensure USB mode is enabled (USB mass storage mode)
        make usb_mode_enable
        log "  • Enabled USB mass storage mode"

        log "BWP configured for USB mass storage mode on Raspberry Pi Zero W"
    else
        log_error "Configuration file not found: $config_file"
        return 1
    fi

    log "BWP configuration completed"
}

# =============================================================================
# Automation Setup
# =============================================================================

setup_automation() {
    log_step "Setting up BWP automation..."

    # Install BWP automation (cron job)
    log "Setting up automated daily wallpaper download..."
    uv run python -m abk_bwp --config desktop_enable

    log "BWP automation configured"
}

# =============================================================================
# Cleanup and Optimization
# =============================================================================

cleanup() {
    log_step "Cleaning up and optimizing system..."

    # Clean package cache
    sudo apt autoremove -y
    sudo apt autoclean

    # Restore original swap size
    if [ -f /etc/dphys-swapfile.bwp_backup ]; then
        log "Restoring original swap configuration..."
        sudo dphys-swapfile swapoff
        sudo mv /etc/dphys-swapfile.bwp_backup /etc/dphys-swapfile
        sudo dphys-swapfile setup
        sudo dphys-swapfile swapon
    fi

    log "Cleanup completed"
}

# =============================================================================
# System Status Check
# =============================================================================

verify_installation() {
    log_step "Verifying BWP installation..."

    # Test BWP import
    if uv run python -c "from abk_bwp import bingwallpaper; print('BWP import successful')"; then
        log "BWP module imports successfully"
    else
        log_error "BWP module import failed"
        return 1
    fi

    # Test basic BWP functionality
    if uv run python -m abk_bwp --help >/dev/null 2>&1; then
        log "BWP CLI working correctly"
    else
        log_error "BWP CLI not working"
        return 1
    fi

    log "BWP installation verified successfully"
}

print_summary() {
    echo
    echo "============================================================================="
    log "BWP Pi Zero W Setup Complete!"
    echo "============================================================================="
    echo
    log_info "Installation Summary:"
    echo "  • BWP installed at: $BWP_DIR"
    echo "  • UV package manager installed"
    echo "  • USB mass storage configured for Frame TV"
    echo "  • System optimized for Pi Zero W"
    echo "  • Daily automation configured"
    echo
    log_info "Next Steps:"
    echo "  1. Reboot the Pi Zero W to activate USB gadget mode:"
    echo "     sudo reboot"
    echo
    echo "  2. Test BWP manually:"
    echo "     cd $BWP_DIR"
    echo "     uv run bwp"
    echo
    echo "  3. Configure Frame TV settings in:"
    echo "     $BWP_DIR/src/abk_bwp/config/ftv_data.toml"
    echo
    echo "  4. Read the setup documentation:"
    echo "     $BWP_DIR/docs/PI_ZERO_SETUP.md"
    echo
    echo "  5. Monitor logs:"
    echo "     tail -f $HOME/logs/bingwallpaper.log"
    echo
    log_info "Setup log saved to: $LOG_FILE"
    echo "============================================================================="
}

# =============================================================================
# Main Execution
# =============================================================================

main() {
    echo "============================================================================="
    echo "               BWP Raspberry Pi Zero W Setup Script"
    echo "============================================================================="
    echo
    log "Starting $SCRIPT_NAME..."
    echo

    # Pre-flight checks
    check_pi_zero
    check_internet
    check_storage

    # System preparation
    update_system
    install_build_dependencies
    optimize_memory

    # USB gadget setup for Frame TV
    setup_usb_gadget

    # Package manager installation
    install_uv
    
    # Setup and configure BWP (run in BWP directory)
    setup_bwp_directory
    (
        cd "$BWP_DIR"
        install_bwp_dependencies
        configure_bwp
        setup_automation
        verify_installation
    )

    # Cleanup and final summary
    cleanup
    print_summary

    log "Setup completed successfully!"
}

# =============================================================================
# Script Entry Point
# =============================================================================

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    log_error "Please run this script as a normal user (not root)"
    log_error "The script will use sudo when needed"
    exit 1
fi

# Check if running on Raspberry Pi
if [ ! -f /proc/cpuinfo ] || ! grep -q "Raspberry Pi" /proc/cpuinfo; then
    log_error "This script is designed for Raspberry Pi hardware"
    exit 1
fi

# Run main function
main "$@"
