# USB Gadget Setup for Frame TV

This document outlines the steps to fix the USB mass storage gadget configuration for Frame TV integration.

## Problem Summary

The Raspberry Pi was not properly configured as a USB gadget, causing the Frame TV to not detect it as a USB storage device.

## Root Causes Fixed

1. **Wrong dwc2 mode**: Changed from `dr_mode=host` to `dr_mode=otg` to enable gadget mode
2. **Missing USB gadget framework**: Added proper configfs setup for modern USB gadget configuration
3. **Incomplete g_mass_storage configuration**: Added disk image file parameter to module configuration
4. **Sudo requirement**: Created helper script to handle USB operations without running entire app as root

## Changes Made

### 1. Updated `setup_pi_zero.sh`
- Fixed dwc2 overlay configuration for OTG mode
- Added proper g_mass_storage module configuration with disk image parameters
- Added modern configfs USB gadget setup
- Added USB helper script installation and sudo configuration

### 2. Created `scripts/usb_helper.sh`
- Helper script for mount/unmount operations requiring elevated privileges
- Handles USB gadget remount operations
- Eliminates need to run entire application as root

### 3. Updated `src/abk_bwp/ftv.py`
- Modified USB operations to use helper script instead of direct sudo calls
- Cleaner separation of privileged operations

## Steps to Apply on Raspberry Pi

### 1. Pull Latest Changes
```bash
cd ~/abk_bwp
git pull
```

### 2. Fix Current Configuration (if already configured)

If you've already run the setup script before, you need to fix the dwc2 configuration:

```bash
# Fix dwc2 overlay configuration
sudo sed -i 's/^dtoverlay=dwc2,dr_mode=host/dtoverlay=dwc2,dr_mode=otg/' /boot/firmware/config.txt

# Verify the change
grep "dtoverlay=dwc2" /boot/firmware/config.txt
```

### 3. Run Updated Setup Script

If this is a fresh setup:
```bash
./setup_pi_zero.sh
```

If you need to update an existing setup, you can run just the USB gadget part:
```bash
# Extract and run just the USB setup functions
# (The setup script is idempotent and safe to re-run)
./setup_pi_zero.sh
```

### 4. Manual Setup (Alternative)

If you prefer to do it manually:

```bash
# Install USB helper script
sudo cp scripts/usb_helper.sh /usr/local/bin/
sudo chmod +x /usr/local/bin/usb_helper.sh

# Configure sudo permissions
echo "$USER ALL=(root) NOPASSWD: /usr/local/bin/usb_helper.sh" | sudo tee /etc/sudoers.d/bwp-usb-helper
sudo chmod 440 /etc/sudoers.d/bwp-usb-helper

# Add user to disk group
sudo usermod -a -G disk $USER
```

### 5. Reboot
```bash
sudo reboot
```

### 6. Test the Setup

After reboot, test the USB gadget:

```bash
# Check if USB gadget is active
lsmod | grep g_mass_storage

# Check USB gadget configuration
ls -la /sys/kernel/config/usb_gadget/

# Test the application (should now work without sudo)
cd ~/abk_bwp
uv run bwp
```

## Verification Steps

1. **USB gadget modules loaded**:
   ```bash
   lsmod | grep g_mass_storage
   ```

2. **USB gadget configured**:
   ```bash
   ls -la /sys/kernel/config/usb_gadget/ftv_gadget/
   ```

3. **Frame TV detection**: Connect the Raspberry Pi to Frame TV via USB and check if it appears as a storage device.

4. **Application runs without sudo**: The BWP application should now run as a normal user.

## Expected Results

- Raspberry Pi appears as USB mass storage device to Frame TV
- BWP application runs without requiring sudo
- Daily image updates work automatically
- Frame TV detects new images after USB remount

## Troubleshooting

If the Frame TV still doesn't detect the USB device:

1. Check dwc2 configuration:
   ```bash
   grep dtoverlay /boot/firmware/config.txt
   ```

2. Check USB gadget status:
   ```bash
   dmesg | grep -i usb
   lsmod | grep dwc2
   lsmod | grep g_mass_storage
   ```

3. Manually test USB gadget:
   ```bash
   sudo /usr/local/bin/usb_helper.sh remount /home/abk/ftv_images/ftv_disk.img
   ```

4. Check if USB cable supports data transfer (not just power)

5. Try different USB ports on the Frame TV