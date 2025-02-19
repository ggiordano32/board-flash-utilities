# Board Flash Utilities

Simple Python scripts for downloading and flashing Linux images to PHYTEC development boards.

## Requirements

- Python 3.x
- PyYAML
- termcolor
- SSH access to remote host

## Quick Start

1. Configure your images in `phyboard_image.yaml`:
```yaml
system_config:
  remote_host: "your-remote-host"
  tftp_path: "/srv/tftp"
  image_extensions: ["wic.xz", "wic.bmap"]
  tftp_files: ["u-boot.img", "tispl.bin", ...]

image_configs:
  - description: "am62x Headless"
    source_path: "/path/to/source"
    base_filename: "phytec-headless-image"
    destination_path: "/path/to/destination"
```

2. Download images:
```bash
./download_images_phyboard.py
```

3. Flash to SD card:
```bash
./flash_py_phyboard.py
```

Just follow the prompts to select your image and target device.
