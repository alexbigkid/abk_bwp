# Samsung Frame TV — RPi Zero USB Gadget Handover

## Context & Goal

Automatically display images on a Samsung Frame TV by having a Raspberry Pi Zero act as a USB mass storage device (thumb drive). The RPi downloads and rotates images daily via a Python project (`abk_bwp`), saves them to a disk image, and presents that image to the TV as if it were a physical USB drive.

**The Samsung TV refuses to mount the USB gadget device.** This document captures all diagnostic findings and the proposed fix.

---

## RPi Zero Environment

- **OS:** Raspbian GNU/Linux 12 (Bookworm)
- **Hostname:** `abk-ftv-lr`
- **User:** `abk`
- **Project repo:** `abk_bwp` (located at `/home/abk/abk_bwp/`)
- **Setup script (deployed):** `/usr/local/bin/setup_ftv_gadget.sh`
- **Systemd service:** `/etc/systemd/system/ftv-usb-gadget.service`
- **Disk image:** `/home/abk/ftv_images/ftv_disk.img`

---

## Disk Image — VERIFIED OK

The backing disk image is correctly configured:

- **Size:** 1 GiB
- **Partition table:** MBR (DOS)
- **Filesystem:** FAT32 (`mkfs.fat`)
- **Contents:** 12 JPG files (~10MB total), plus `DCIM/`, `Pictures/`, `README.txt`
- **Mount test:** Mounts fine on the Pi via loopback

No changes needed to the disk image.

---

## USB Gadget Configuration — PROBLEMS FOUND

### Current (broken) configuration:

```
idVendor:     0x1d6b  (Linux Foundation)
idProduct:    0x0104  (Multifunction Composite Gadget)
manufacturer: "Raspberry Pi Foundation"
product:      "Frame TV USB Storage"
bcdDevice:    0x0100
bcdUSB:       0x0200
removable:    1  (correct)
ro:           0  (correct)
cdrom:        0  (correct)
```

### Root Cause Analysis

Samsung Frame TVs likely filter USB devices by vendor/product ID or device descriptor strings. The current configuration identifies itself as a Linux Foundation Composite Gadget made by Raspberry Pi Foundation — no real thumb drive presents itself this way. The TV sees this and ignores it.

### The Fix — Spoof as a SanDisk Cruzer Blade

Change the USB descriptor to match a real consumer thumb drive:

| Field | Old (broken) | New (fix) |
|-------|-------------|-----------|
| idVendor | `0x1d6b` (Linux Foundation) | `0x0781` (SanDisk) |
| idProduct | `0x0104` (Composite Gadget) | `0x5567` (Cruzer Blade) |
| manufacturer | "Raspberry Pi Foundation" | "SanDisk" |
| product | "Frame TV USB Storage" | "Cruzer Blade" |

All other settings (removable=1, ro=0, cdrom=0, FAT32 image) remain the same.

### If Spoofing VID/PID Alone Doesn't Work

Try also setting the SCSI inquiry string on the LUN:

```bash
echo "SanDisk Cruzer Blade    1.00" > functions/mass_storage.usb0/lun.0/inquiry_string
```

### Alternative VID/PIDs to Try

If SanDisk doesn't work, try these known-good USB drive identities:

| Brand | VID | PID | Product |
|-------|-----|-----|---------|
| SanDisk Cruzer Blade | 0x0781 | 0x5567 | Cruzer Blade |
| Samsung BAR Plus | 0x090c | 0x1000 | Flash Drive |
| Kingston DataTraveler | 0x0951 | 0x1666 | DataTraveler |

---

## Fixed Setup Script

```bash
#!/bin/bash
# USB Gadget setup script for Frame TV
# Spoofs as SanDisk Cruzer Blade for Samsung TV compatibility

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

# Configure USB device descriptor — spoof as SanDisk Cruzer Blade
echo 0x0781 > idVendor    # SanDisk
echo 0x5567 > idProduct   # Cruzer Blade
echo 0x0100 > bcdDevice   # v1.0.0
echo 0x0200 > bcdUSB      # USB2

# Configure device strings
mkdir -p strings/0x409
echo "SanDisk" > strings/0x409/manufacturer
echo "Cruzer Blade" > strings/0x409/product
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

echo "USB gadget configured successfully (spoofed as SanDisk Cruzer Blade)"
```

---

## Systemd Service (no changes needed)

```ini
[Unit]
Description=Frame TV USB Gadget Setup
After=network.target
Wants=network.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/setup_ftv_gadget.sh /home/abk/ftv_images/ftv_disk.img
RemainAfterExit=yes
User=root

[Install]
WantedBy=multi-user.target
```

---

## Teardown Procedure (if gadget needs reconfiguring)

```bash
sudo bash -c '
GADGET_DIR="/sys/kernel/config/usb_gadget/ftv_gadget"
echo "" > $GADGET_DIR/UDC
rm $GADGET_DIR/configs/c.1/mass_storage.usb0
rmdir $GADGET_DIR/configs/c.1/strings/0x409
rmdir $GADGET_DIR/configs/c.1
rmdir $GADGET_DIR/functions/mass_storage.usb0
rmdir $GADGET_DIR/strings/0x409
rmdir $GADGET_DIR
'
```

---

## RPi Zero OS Reinstall Notes

When reinstalling the OS on the RPi Zero:

1. Flash Raspbian Bookworm Lite (no desktop needed)
2. Enable SSH and configure WiFi in the imager
3. Ensure `dwc2` overlay is enabled in `/boot/firmware/config.txt`:
   ```
   dtoverlay=dwc2
   ```
4. Ensure `dwc2` is in `/etc/modules`:
   ```
   dwc2
   ```
5. Clone the `abk_bwp` project and run the setup
6. Deploy the **fixed** `setup_ftv_gadget.sh` (with SanDisk spoofing)
7. Install and enable the systemd service

---

## Alternative Approaches If USB Spoofing Fails

If Samsung still won't mount even with spoofed VID/PID:

1. **HDMI direct display:** Connect RPi to TV via HDMI, run fullscreen slideshow with `feh` or Chromium kiosk mode. Loses art mode matte look but gives full control.

2. **Samsung WebSocket API:** Use `samsung-tv-ws-api` Python library to upload images over the network. Works on some model years but Samsung has been restricting this on newer firmware.

3. **Switch TV brands:** TCL NXTFRAME and Hisense CanvasTV both run Google TV and are generally more permissive with USB devices. Skyworth Canvas supports Crestron/Control4 for programmatic control.

4. **LG Gallery TV (2026):** Runs webOS, supports personal photos via Gallery+ and USB. Not yet available but worth watching.

---

## Research: Art TV Market (Feb 2026)

| TV | Upload Method | API/Automation | Notes |
|---|---|---|---|
| Samsung Frame/Frame Pro | SmartThings app, USB, WebSocket API (unofficial) | Best ecosystem via `samsung-tv-ws-api` Python lib, but Samsung restricting access | Most mature but most restrictive |
| TCL NXTFRAME | USB, TCL Art Gallery app | No known API | Google TV — sideloading possible |
| Hisense CanvasTV | USB (PNG), built-in art app | No API access (confirmed by Hisense) | Free art library, no subscription |
| LG Gallery TV | LG app, USB, Gallery+ service | No known API yet | New for 2026, webOS based |
| Skyworth Canvas/Elite | USB, Google Photos | Crestron/Control4 support | Best for custom integrators |
