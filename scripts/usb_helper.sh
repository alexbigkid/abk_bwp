#!/bin/bash
# =============================================================================
# USB Helper Script for Frame TV Operations
# =============================================================================
# This script handles USB operations that require elevated privileges
# Called by the BWP application for USB disk operations

set -e

LOG_PREFIX="[usb_helper]"

log() {
    echo "$LOG_PREFIX $1" >&2
}

error() {
    echo "$LOG_PREFIX ERROR: $1" >&2
    exit 1
}

# =============================================================================
# USB Disk Operations
# =============================================================================

mount_usb_disk() {
    local disk_image="$1"
    local mount_point="$2"
    
    if [ -z "$disk_image" ] || [ -z "$mount_point" ]; then
        error "Usage: mount_usb_disk <disk_image> <mount_point>"
    fi
    
    if [ ! -f "$disk_image" ]; then
        error "Disk image not found: $disk_image"
    fi
    
    log "Setting up loop device for $disk_image"
    local loop_device
    loop_device=$(losetup --find --show "$disk_image")
    
    log "Mounting $loop_device to $mount_point"
    mkdir -p "$mount_point"
    mount -o uid=1000,gid=1000 "$loop_device" "$mount_point"
    
    echo "$loop_device"
}

unmount_usb_disk() {
    local mount_point="$1"
    local loop_device="$2"
    
    if [ -z "$mount_point" ]; then
        error "Usage: unmount_usb_disk <mount_point> [loop_device]"
    fi
    
    log "Unmounting $mount_point"
    if mountpoint -q "$mount_point"; then
        umount "$mount_point" || true
    fi
    
    if [ -n "$loop_device" ] && [ -e "$loop_device" ]; then
        log "Detaching loop device $loop_device"
        losetup --detach "$loop_device" || true
    fi
    
    if [ -d "$mount_point" ]; then
        rmdir "$mount_point" 2>/dev/null || true
    fi
}

remount_usb_gadget() {
    local disk_image="$1"
    
    if [ -z "$disk_image" ]; then
        error "Usage: remount_usb_gadget <disk_image>"
    fi
    
    log "Reloading USB mass storage gadget"
    
    # Remove g_mass_storage module
    if lsmod | grep -q g_mass_storage; then
        log "Removing g_mass_storage module"
        rmmod g_mass_storage || true
        sleep 1
    fi
    
    # Reload g_mass_storage module with disk image
    log "Loading g_mass_storage module with $disk_image"
    modprobe g_mass_storage file="$disk_image" removable=1 ro=0 stall=0
    
    log "USB gadget remount completed"
}

# =============================================================================
# Main Command Processing
# =============================================================================

case "${1:-}" in
    mount)
        mount_usb_disk "$2" "$3"
        ;;
    unmount)
        unmount_usb_disk "$2" "$3"
        ;;
    remount)
        remount_usb_gadget "$2"
        ;;
    *)
        echo "Usage: $0 {mount|unmount|remount} [args...]"
        echo ""
        echo "Commands:"
        echo "  mount <disk_image> <mount_point>  - Mount USB disk image"
        echo "  unmount <mount_point> [loop_dev]  - Unmount USB disk"
        echo "  remount <disk_image>              - Remount USB gadget"
        exit 1
        ;;
esac