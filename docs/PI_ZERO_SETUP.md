# Raspberry Pi Zero W Setup Guide for BWP

This guide helps you set up BWP (Bing Wallpaper) on a Raspberry Pi Zero W with Frame TV integration.

> **📖 Main Documentation**: For general BWP information and macOS setup, see the [main README](../README.md).

## Prerequisites

- **Hardware**: Raspberry Pi Zero W (any version)
- **SD Card**: 32GB microSD card (minimum 16GB)
- **OS**: Raspberry Pi OS Lite (32-bit) - recommended
- **Network**: WiFi configured and working
- **SSH**: Enabled for remote access

## Quick Setup (Automated)

### 1. Clone Repository and Run Setup Script

```bash
# Clone the BWP repository
git clone https://github.com/alexbigkid/abk_bwp.git

# Change to the repository directory
cd abk_bwp

# Make the setup script executable
chmod +x setup_pi_zero.sh

# Run the setup (will take 30-60 minutes on Pi Zero W)
./setup_pi_zero.sh
```

### 2. Reboot and Test

```bash
# Reboot to activate USB gadget mode
sudo reboot

# After reboot, test BWP (from the repository directory)
cd abk_bwp
uv run bwp --help
```

## What the Script Does

### System Preparation
- ✅ Updates all system packages
- ✅ Installs build tools and dependencies
- ✅ Installs Pillow (PIL) image processing libraries
- ✅ Optimizes memory settings for Pi Zero W
- ✅ Increases swap temporarily for compilation

### USB Mass Storage Setup
- ✅ Enables USB gadget mode (`dwc2` overlay)
- ✅ Configures mass storage module (`g_mass_storage`)
- ✅ Creates 1GB disk image for Frame TV
- ✅ Formats disk image as FAT32

### BWP Installation
- ✅ Installs UV package manager (fast Python package management)
- ✅ Clones BWP repository
- ✅ Offers two installation modes:
  - **USB Mode**: Lightweight, for USB-only Frame TV connection
  - **Full Mode**: USB + HTTP for network Frame TV connection
- ✅ Configures BWP for Pi Zero W environment

### Automation Setup
- ✅ Sets up daily cron job for automatic wallpaper downloads
- ✅ Configures logging

### Optimization
- ✅ Cleans up temporary files
- ✅ Restores original swap settings
- ✅ Optimizes GPU memory for headless operation

## Manual Setup (Alternative)

If you prefer manual installation or the script fails:

### 1. Install System Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install build dependencies
sudo apt install -y \
    build-essential git curl python3-dev \
    libjpeg-dev zlib1g-dev libfreetype6-dev libwebp-dev

# Install UV package manager
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
```

### 2. Enable USB Gadget Mode

```bash
# Enable USB gadget in boot config
echo "dtoverlay=dwc2" | sudo tee -a /boot/config.txt

# Enable mass storage module
echo "g_mass_storage" | sudo tee -a /etc/modules

# Create disk image for Frame TV
mkdir -p ~/ftv_images
dd if=/dev/zero of=~/ftv_images/ftv_disk.img bs=1M count=1024
sudo mkfs.vfat ~/ftv_images/ftv_disk.img
```

### 3. Install BWP

```bash
# Clone repository
git clone https://github.com/alexbigkid/abk_bwp.git
cd abk_bwp

# Install dependencies (choose one)
uv sync                    # USB mode only (lightweight)
uv sync --extra frametv    # Full mode with HTTP support

# Test installation
uv run bwp --help
```

### 4. Setup Automation

```bash
# Enable daily automation
uv run python -m abk_bwp --config desktop_enable
```

## Configuration

### BWP Configuration

Edit `src/abk_bwp/config/bwp_config.toml`:

```toml
[ftv]
enabled = true
usb_mode = true  # Enable for Pi Zero USB mode

[desktop_img]
enabled = true

# Set image size for your Frame TV
image_width = 1920
image_height = 1080
```

### Frame TV Configuration

Edit `src/abk_bwp/config/ftv_data.toml` for your Frame TV details:

```toml
[ftv_data.your_tv_name]
ip_addr = "192.168.1.100"  # Your Frame TV IP
mac_addr = "AA:BB:CC:DD:EE:FF"  # Your Frame TV MAC
port = 8001
api_token_file = "your_tv_token.txt"
img_rate = 24  # Hours between image changes
```

## Troubleshooting

### Pillow Compilation Fails
```bash
# Install missing dependencies
sudo apt install -y libjpeg-dev zlib1g-dev libfreetype6-dev

# Increase swap temporarily
sudo dphys-swapfile swapoff
sudo sed -i 's/CONF_SWAPSIZE=100/CONF_SWAPSIZE=1024/' /etc/dphys-swapfile
sudo dphys-swapfile setup && sudo dphys-swapfile swapon

# Try again
uv sync
```

### UV Package Manager Issues
```bash
# Reinstall UV
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
```

### USB Gadget Not Working
```bash
# Check if modules are loaded
lsmod | grep dwc2
lsmod | grep g_mass_storage

# Check boot config
grep dwc2 /boot/config.txt
grep g_mass_storage /etc/modules

# Reboot if changes were made
sudo reboot
```

### BWP Not Running
```bash
# Check logs
tail -f ~/logs/bingwallpaper.log

# Test manually
cd ~/abk_bwp
uv run python -m abk_bwp

# Check cron job
crontab -l
```

## Performance Optimization

### Memory Management
- **Swap**: Temporarily increased to 1024MB during installation
- **GPU Memory**: Reduced to 16MB for headless operation
- **USB Mode**: Uses less memory than HTTP mode

### Storage Optimization
- **Clean Cache**: Run `sudo apt autoremove && sudo apt autoclean`
- **Log Rotation**: BWP logs are automatically rotated
- **Image Cleanup**: Old wallpapers are automatically cleaned up

## Frame TV Integration Modes

### USB Mode (Recommended for Pi Zero W)
- **Pros**: Lower memory usage, no network dependency, faster
- **Cons**: Requires physical USB connection to Frame TV
- **Setup**: Pi Zero W acts as USB mass storage device

### HTTP Mode
- **Pros**: Wireless operation, remote control
- **Cons**: Higher memory usage, requires stable WiFi
- **Setup**: Network communication with Frame TV

## Security Considerations

- **SSH Keys**: Use SSH key authentication instead of passwords
- **UFW Firewall**: Enable if using HTTP mode
- **Regular Updates**: Keep system and BWP updated
- **Strong Passwords**: Use strong passwords for all accounts

## Maintenance

### Regular Updates
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Update BWP
cd ~/abk_bwp
git pull
uv sync
```

### Monitor Performance
```bash
# Check memory usage
free -h

# Check CPU temperature
vcgencmd measure_temp

# Check disk usage
df -h
```

### Backup Configuration
```bash
# Backup BWP config
cp -r ~/abk_bwp/src/abk_bwp/config ~/abk_bwp_config_backup

# Backup system config
sudo cp /boot/config.txt /boot/config.txt.backup
```

## Support

- **Repository**: https://github.com/alexbigkid/abk_bwp
- **Issues**: Report bugs and feature requests on GitHub
- **Logs**: Check `~/logs/bingwallpaper.log` for debugging

## Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **RAM** | 512MB (Pi Zero W) | 512MB |
| **Storage** | 16GB microSD | 32GB microSD (Class 10) |
| **CPU** | ARM11 (Pi Zero W) | ARM11 |
| **Network** | WiFi 802.11n | WiFi 802.11n |
| **Power** | 5V 1A | 5V 1.5A (with USB peripherals) |

The setup script automatically optimizes for Pi Zero W's limited resources while maintaining full BWP functionality.