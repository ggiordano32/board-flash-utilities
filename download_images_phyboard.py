#!/usr/bin/env python3

import yaml
import os
import sys
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Set
from dataclasses import dataclass

@dataclass
class SystemConfig:
    image_extensions: List[str]
    tftp_files: List[str]
    tftp_path: str
    remote_host: str

@dataclass
class ImageConfig:
    description: str
    source_path: str
    base_filename: str
    destination_path: str

class PhyboardDownloader:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.configs: List[ImageConfig] = []
        self.system_config: SystemConfig = None

    def load_config(self) -> None:
        """Load and parse the YAML configuration file."""
        try:
            with open(self.config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            # Load system configuration
            sys_config = config_data.get('system_config', {})
            self.system_config = SystemConfig(
                image_extensions=sys_config.get('image_extensions', []),
                tftp_files=sys_config.get('tftp_files', []),
                tftp_path=sys_config.get('tftp_path', '/srv/tftp'),
                remote_host=sys_config.get('remote_host', 'ls-strontium.phytec')
            )
            
            # Load image configurations
            self.configs = [
                ImageConfig(**config) for config in config_data['image_configs']
            ]
        except FileNotFoundError:
            print(f"Error: Configuration file {self.config_path} not found.")
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"Error parsing configuration file: {e}")
            sys.exit(1)

    def show_configurations(self) -> None:
        """Display available configurations to the user."""
        print("\nAvailable configurations:")
        for idx, config in enumerate(self.configs, 1):
            print(f"\n{idx}. Description: {config.description}")
            print(f"   Source: {config.source_path}")
            print(f"   Base Filename: {config.base_filename}")
            print(f"   Destination: {config.destination_path}")
            print("   " + "-" * 40)

    def process_filename(self, base_filename: str, extension: str, name_append: str) -> str:
        """Generate the final filename based on user input."""
        if name_append:
            return f"{base_filename}-{name_append}.{extension}"
        return f"{base_filename}.{extension}"

    def get_remote_file_size(self, source: str) -> int:
        """Get the size of a remote file using ssh and ls, following symbolic links."""
        try:
            # Use ls -L to follow symbolic links and get the actual file size
            cmd = ['ssh', self.system_config.remote_host, f'ls -L -l "{source}" | awk \'{{print $5}}\'']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                size = result.stdout.strip()
                try:
                    return int(size)
                except ValueError:
                    print(f"Debug: Could not convert '{size}' to integer")
                    return 0
            else:
                # Let's also try to see what the symlink points to
                cmd_readlink = ['ssh', self.system_config.remote_host, f'readlink -f "{source}"']
                result_link = subprocess.run(cmd_readlink, capture_output=True, text=True)
                if result_link.returncode == 0:
                    print(f"Debug: File is symlink pointing to: {result_link.stdout.strip()}")
                return 0
                
        except Exception as e:
            print(f"Debug: Exception occurred: {e}")
            return 0

    def get_local_file_size(self, path: str) -> int:
        """Get the size of a local file."""
        try:
            return os.path.getsize(path)
        except Exception:
            return 0

    def copy_file(self, source: str, destination: str) -> bool:
        """Copy a file using SCP with simple progress monitoring."""
        try:
            # Create destination directory if it doesn't exist
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            
            # Get remote file size before transfer
            remote_size = self.get_remote_file_size(source)
            
            print(f"\nStarting transfer of: {os.path.basename(source)}")
            if remote_size > 0:
                print(f"File size: {remote_size / 1024 / 1024:.2f} MB")
            
            start_time = time.time()
            
            # Use scp with verbose flag for debugging
            cmd = ['scp', '-v', f"{self.system_config.remote_host}:{source}", destination]
            print(f"Debug: Running command: {' '.join(cmd)}")
            
            # Run SCP
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Verify the file exists and has content
                if os.path.exists(destination):
                    final_size = os.path.getsize(destination)
                    if final_size > 0:
                        elapsed_time = time.time() - start_time
                        speed = final_size / (1024 * 1024 * elapsed_time) if elapsed_time > 0 else 0
                        print(f"\rTransfer complete: {final_size / 1024 / 1024:.2f} MB ({speed:.2f} MB/s)")
                        print(f"Successfully copied: {destination}")
                        print(f"Time taken: {elapsed_time:.1f} seconds")
                        return True
                    else:
                        print(f"Error: File was created but is empty: {destination}")
                        return False
                else:
                    print(f"Error: File was not created: {destination}")
                    return False
            else:
                print(f"Error during transfer:")
                print(f"stdout: {result.stdout}")
                print(f"stderr: {result.stderr}")
                return False
                    
        except subprocess.CalledProcessError as e:
            print(f"Error copying file: {e}")
            print(f"stderr: {e.stderr}")
            return False
        except KeyboardInterrupt:
            print("\nTransfer interrupted by user")
            if os.path.exists(destination):
                os.remove(destination)
            return False
        except Exception as e:
            print(f"Unexpected error: {e}")
            return False

    def ensure_tftp_permissions(self):
        """Ensure TFTP directory exists and has correct permissions."""
        try:
            if not os.path.exists(self.system_config.tftp_path):
                os.makedirs(self.system_config.tftp_path, exist_ok=True)
            # Set permissions to 777 for TFTP directory
            os.chmod(self.system_config.tftp_path, 0o777)
        except Exception as e:
            print(f"Error setting up TFTP directory: {e}")
            sys.exit(1)

    def download_images(self, selected_config: ImageConfig, name_append: str = "") -> None:
        """Download all image files for the selected configuration."""
        # Ensure directories exist
        os.makedirs(selected_config.destination_path, exist_ok=True)
        self.ensure_tftp_permissions()

        # First, handle normal image files
        print("\nDownloading image files...")
        for ext in self.system_config.image_extensions:
            print(f"\nProcessing file with extension: {ext}")
            source = f"{selected_config.source_path}/{selected_config.base_filename}.{ext}"
            dest_filename = self.process_filename(selected_config.base_filename, ext, name_append)
            destination = os.path.join(selected_config.destination_path, dest_filename)
            
            self.copy_file(source, destination)

        # Then, handle TFTP files
        print("\nDownloading boot files to TFTP directory...")
        for file in self.system_config.tftp_files:
            print(f"\nProcessing TFTP file: {file}")
            source = f"{selected_config.source_path}/{file}"
            destination = os.path.join(self.system_config.tftp_path, file)
            
            self.copy_file(source, destination)

def main():
    config_path = 'phyboard_image.yaml'
    if not os.path.exists(config_path):
        print(f"Error: Configuration file {config_path} not found.")
        sys.exit(1)

    downloader = PhyboardDownloader(config_path)
    downloader.load_config()
    downloader.show_configurations()

    try:
        choice = int(input("\nEnter the number of your choice: ")) - 1
        if not 0 <= choice < len(downloader.configs):
            print("Invalid selection")
            sys.exit(1)

        name_append = input("\nEnter a name to append to the filenames "
                          "(or press Enter to keep original names): ").strip()

        selected_config = downloader.configs[choice]
        downloader.download_images(selected_config, name_append)

    except ValueError:
        print("Please enter a valid number")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)

if __name__ == "__main__":
    main()
