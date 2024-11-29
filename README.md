# Endoscope
Git Repository for Endoscope Project

## Configuration
Requires: U2D2, U2D2 PHB, TTY Connector (x2), Dynamixel, Micro-USB to USB-A.
Software: DynamixelSDK ([source](https://github.com/ROBOTIS-GIT/DynamixelSDK)), I used Arch Linux in WSL2 (note that this requires further configuration)

### Arch Linux WSL2
- On Windows-side: 
	- Install `usbipd` tool from [here](https://github.com/dorssel/usbipd-win) and:
		- Bind the USB device with `gsudo usbipd bind --busid=<BUSID>` (needs to be done with administrative privileges, hence the `gsudo`)
		- Attach the USB device to WSL with `usbipd attach --wsl --busid=<BUSID>` (does not require administrative privileges)
- On Linux-side: 
	- Get the DynamixelSDK and run the setup
		- Note that the tutorial attempts to install the packages in the system Python installation, using a virtual environment is possible: simply omit the `sudo` and work when the `venv` has been sourced
	- Attempt to run the `read_write.py` script
		- This may not have execution permissions: `sudo chmod +x read_write.py`
		- The user may not have permission to use the USB device: `sudo chmod 666 /dev/tty<USBX>`

> [!note]
> You may need to detach the USB device from WSL to re-use it in Windows, see `usbipd` documentation

