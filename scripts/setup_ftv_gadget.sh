#!/bin/bash
# USB Gadget setup script for Frame TV.
# Spoofs as SanDisk Cruzer Blade for Samsung TV compatibility.
# Samsung Frame TVs filter USB devices by vendor/product ID and SCSI inquiry
# strings, ignoring anything that looks like a generic Linux gadget.

set -e

GADGET_DIR="/sys/kernel/config/usb_gadget/ftv_gadget"
DISK_IMAGE="$1"

if [ -z "$DISK_IMAGE" ]; then
    echo "Usage: $0 <path-to-disk-image>" >&2
    exit 1
fi

if [ ! -f "$DISK_IMAGE" ]; then
    echo "Disk image not found: $DISK_IMAGE" >&2
    exit 1
fi

# Ensure configfs is mounted
if ! mountpoint -q /sys/kernel/config; then
    mount -t configfs none /sys/kernel/config
fi

# Check if gadget already exists
if [ -d "$GADGET_DIR" ]; then
    echo "USB gadget already configured"
    exit 0
fi

# Create the gadget directory
mkdir -p "$GADGET_DIR"
cd "$GADGET_DIR"

# Configure USB device descriptor — spoof as SanDisk Cruzer Blade
echo 0x0781 > idVendor    # SanDisk
echo 0x5567 > idProduct   # Cruzer Blade
echo 0x0100 > bcdDevice   # v1.0.0
echo 0x0200 > bcdUSB      # USB2

# Configure device strings
mkdir -p strings/0x409
echo "SanDisk" > strings/0x409/manufacturer
echo "Cruzer Blade" > strings/0x409/product
echo "$(grep Serial /proc/cpuinfo | cut -d ' ' -f 2)" > strings/0x409/serialnumber

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
# SCSI inquiry string — max 28 chars: 8 vendor + 16 product + 4 rev
echo "SanDisk Cruzer Blade    1.00" > functions/mass_storage.usb0/lun.0/inquiry_string
echo "$DISK_IMAGE" > functions/mass_storage.usb0/lun.0/file

# Link function to configuration
ln -s functions/mass_storage.usb0 configs/c.1/

# Enable gadget
UDC=$(ls /sys/class/udc | head -1)
if [ -z "$UDC" ]; then
    echo "ERROR: No UDC found in /sys/class/udc — is dwc2 loaded in OTG mode?" >&2
    exit 1
fi
echo "$UDC" > UDC

echo "USB gadget configured successfully (spoofed as SanDisk Cruzer Blade)"
