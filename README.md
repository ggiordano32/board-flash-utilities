# Board Flash Utilities
These are a set of scripts to assist in downloading and flashing PHYTEC SoMs.
The scripts have a util

### Dependencies
These scripts use bmap tools. If they are not installed they can be added with the following:
```sh
sudo apt update && sudo apt install bmap-tools
```

## How to Use
Begin by checking out the project and then proceed with the following:
1. Make the files executable
``` sh
chmod 755 board-flash-utilities/*
```
2. Move them to the local binaries folder
``` sh
sudo cp board-flash-utilities/* /usr/local/bin/
```

# Descriptions

## 1 - Download Scripts
 - **download_phyboard_image**

   _Downloads wic.xz and wic.bmap files from our server to our local machine._

 - **download_phyboard_image-p**

    _Same as download_phyboard_image but it downloads tispl, tiboot3, and u-boot files as well_

 - **download_phyboard_image.config**

    _Config file for where files should be downloaded and stored_

## 2 - Flash Script
 - **flash_phyboard**

    _Flashes bmap files from the downloads folder to a selected /dev/sd* device_

- **flash_directories.config**

    _Configuries which folders to look for images to be flashed_
