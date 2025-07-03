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
BWP_REPO="https://github.com/alexbigkid/abk_bwp.git"
BWP_DIR="$HOME/abk_bwp"
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

setup_usb_gadget() {
    log_step "Setting up USB mass storage gadget for Frame TV..."

    # Enable dwc2 overlay for USB gadget mode
    if ! grep -q "^dtoverlay=dwc2" /boot/config.txt; then
        log "Enabling USB gadget mode..."
        echo "dtoverlay=dwc2" | sudo tee -a /boot/config.txt > /dev/null
    fi

    # Enable g_mass_storage module
    if ! grep -q "g_mass_storage" /etc/modules; then
        echo "g_mass_storage" | sudo tee -a /etc/modules > /dev/null
        log "USB mass storage module enabled"
    fi

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

clone_bwp() {
    log_step "Cloning BWP repository..."

    if [ -d "$BWP_DIR" ]; then
        log "BWP directory exists, pulling latest changes..."
        cd "$BWP_DIR"
        git pull
    else
        log "Cloning BWP from $BWP_REPO..."
        git clone "$BWP_REPO" "$BWP_DIR"
        cd "$BWP_DIR"
    fi

    log "BWP repository ready at: $BWP_DIR"
}

install_bwp_dependencies() {
    log_step "Installing BWP dependencies..."

    cd "$BWP_DIR"

    # Check if user wants Frame TV HTTP mode
    echo
    log_info "BWP Installation Options:"
    echo "  1) USB Mode Only (for Frame TV USB connection) - Lightweight"
    echo "  2) Full Mode (USB + HTTP for Frame TV network connection)"
    echo
    read -r -p "Select installation type [1-2]: " install_choice

    case $install_choice in
        1)
            log "Installing BWP in USB mode (lightweight)..."
            uv sync
            ;;
        2)
            log "Installing BWP with Frame TV HTTP support..."
            uv sync --extra frametv
            ;;
        *)
            log_warning "Invalid choice, defaulting to USB mode..."
            uv sync
            ;;
    esac

    log "BWP dependencies installed successfully"
}

configure_bwp() {
    log_step "Configuring BWP for Pi Zero W..."

    cd "$BWP_DIR"

    # Copy default configuration if not exists
    local config_file="src/abk_bwp/config/bwp_config.toml"
    if [ -f "$config_file" ]; then
        # Enable USB mode by default for Pi Zero
        log "Configuring BWP for USB mode..."

        # Create a backup and enable USB mode
        cp "$config_file" "${config_file}.backup"

        # Enable USB mode in FTV config (if not already enabled)
        if ! grep -q "usb_mode.*=.*true" "$config_file"; then
            log "Enabling USB mode in BWP configuration..."
            # This would need to be adjusted based on actual config structure
            log_info "Please manually enable usb_mode = true in $config_file"
        fi
    fi

    log "BWP configuration completed"
}

# =============================================================================
# Automation Setup
# =============================================================================

setup_automation() {
    log_step "Setting up BWP automation..."

    cd "$BWP_DIR"

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

    cd "$BWP_DIR"

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

    # Package manager and BWP installation
    install_uv
    clone_bwp
    install_bwp_dependencies
    configure_bwp

    # Automation setup
    setup_automation

    # Cleanup and verification
    cleanup
    verify_installation

    # Final summary
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
