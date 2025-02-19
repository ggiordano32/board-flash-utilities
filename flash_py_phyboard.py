#!/usr/bin/env python3

import os
from flash_utils import (
    read_directories, list_bmap_files, get_human_readable_size,
    list_devices, list_mounted_partitions, unmount_partitions, flash_image
)
from termcolor import colored

def select_directory(directories):
    print("Please select a directory to enumerate bmap files from:")
    for idx, dir in enumerate(directories):
        print(f"{idx + 1}) {dir}")
    dir_selection = int(input("Enter the number of the directory: ")) - 1
    return directories[dir_selection]

def select_bmap_file(bmap_files):
    print("Please select a bmap file (corresponding wic.xz file sizes are shown in yellow):")
    for idx, bmap_file in enumerate(bmap_files):
        wic_file = bmap_file.replace('.bmap', '.xz')
        if os.path.exists(wic_file):
            file_size = get_human_readable_size(wic_file)
        else:
            file_size = "Unknown size"
        print(f"{idx + 1}) {bmap_file} {colored(f'({file_size})', 'yellow')}")
    bmap_selection = int(input("Enter the number of the bmap file: ")) - 1
    return bmap_files[bmap_selection]

def select_device(devices, mounted_partitions):
    print("\nPlease select a device to flash (devices with * are mounted):")
    for idx, device in enumerate(devices):
        mount_status = " * (Mounted: " + ", ".join([f"{part}:{mnt}" for part, mnt in mounted_partitions.items() if part.startswith(device)]) + ")" if any(part.startswith(device) for part in mounted_partitions) else ""
        print(f"{idx + 1}) {device}{mount_status}")
    device_selection = int(input("Enter the number of the device: ")) - 1
    return devices[device_selection]

# Define the path to the flash_directories_py.config file
script_dir = os.path.dirname(os.path.abspath(__file__))
directories_file = os.path.join(script_dir, 'flash_directories_py.config')

# Read directories from the config file
directories = read_directories(directories_file)

# Main script execution
selected_dir = select_directory(directories)
bmap_files = list_bmap_files(selected_dir)
selected_bmap_file = select_bmap_file(bmap_files)
selected_wic_file = selected_bmap_file.replace('.bmap', '.xz')
devices = list_devices()
mounted_partitions = list_mounted_partitions()
selected_device = select_device(devices, mounted_partitions)

print(f"\nYou are about to flash the image: {os.path.basename(selected_wic_file)}")
print(f"To the device: {selected_device}")
confirmation = input("Are you sure? (Y/n): ").lower()
if confirmation not in ('y', 'yes', ''):
    print("Operation aborted by user.")
    exit(1)

unmount_partitions(selected_device, mounted_partitions)
flash_image(selected_bmap_file, selected_wic_file, selected_device)
