import os

if os.name == 'nt':
    import msvcrt
    def getch():
        return msvcrt.getch().decode()
else:
    import sys, tty, termios
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    def getch():
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

from dynamixel_sdk import * # Uses Dynamixel SDK library

# Configuration for DYNAMIXEL XM430-W350-T
ADDR_OPERATING_MODE         = 11
ADDR_VELOCITY_LIMIT         = 44
ADDR_TORQUE_ENABLE          = 64
ADDR_GOAL_POSITION          = 116
ADDR_GOAL_VELOCITY          = 104
ADDR_PRESENT_CURRENT        = 126
ADDR_PRESENT_VELOCITY       = 128
ADDR_PRESENT_POSITION       = 132
DXL_MINIMUM_POSITION_VALUE  = 0             # Refer to the Minimum Position Limit of product eManual
DXL_MAXIMUM_POSITION_VALUE  = 4095          # Refer to the Maximum Position Limit of product eManual
BAUDRATE                    = 57600

# DYNAMIXEL Protocol Version (1.0 / 2.0)
# https://emanual.robotis.com/docs/en/dxl/protocol2/
PROTOCOL_VERSION            = 2.0

# Factory default ID of all DYNAMIXEL is 1
DXL_ID                      = 1

# Use the actual port assigned to the U2D2.
# ex) Windows: "COM*", Linux: "/dev/ttyUSB*", Mac: "/dev/tty.usbserial-*"
DEVICENAME                  = '/dev/ttyUSB0'

TORQUE_ENABLE               = 1     # Value for enabling the torque
TORQUE_DISABLE              = 0     # Value for disabling the torque
DXL_MOVING_STATUS_THRESHOLD = 20    # Dynamixel moving status threshold

# Operating mode values
CURRENT_CONTROL_MODE        = 0
VELOCITY_CONTROL_MODE       = 1
POSITION_CONTROL_MODE       = 3

index = 0
dxl_goal_position = [DXL_MINIMUM_POSITION_VALUE, DXL_MAXIMUM_POSITION_VALUE]         # Goal position


# Initialize PortHandler instance
# Set the port path
# Get methods and members of PortHandlerLinux or PortHandlerWindows
portHandler = PortHandler(DEVICENAME)

# Initialize PacketHandler instance
# Set the protocol version
# Get methods and members of Protocol1PacketHandler or Protocol2PacketHandler
packetHandler = PacketHandler(PROTOCOL_VERSION)

def handle_write_confirmation(dxl_comm_result, dxl_error):
    if dxl_comm_result != COMM_SUCCESS:
        print("%s" % packetHandler.getTxRxResult(dxl_comm_result))
    elif dxl_error != 0:
        print("%s" % packetHandler.getRxPacketError(dxl_error))
    else:
        print("Message is sent")

def convert_raw_current_to_mA(raw_current):
    """Convert raw current value to mA
    Formula from Dynamixel manual: Current(mA) = Raw Current * 2.69 (mA)"""
    return raw_current * 2.69

def print_status(speed_percentage, direction, current_mA):
    """Print the current status in a simple line format"""
    print(f"Direction: {direction:<10} | Speed: {speed_percentage:>3}% | Current: {current_mA:>6.1f} mA")

def setup_dynamixel():
    """Setup the Dynamixel motor"""
    if not portHandler.openPort():
        print("Failed to open port")
        return False

    if not portHandler.setBaudRate(BAUDRATE):
        print("Failed to change baudrate")
        return False

    # Disable torque to change operating mode
    packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, 0)

    # Set velocity control mode
    packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_OPERATING_MODE, VELOCITY_CONTROL_MODE)

    # Enable torque
    packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, 1)

    return True

def set_velocity(velocity):
    """Set velocity of motor. Range is 0 to 200 RPM"""

    # Convert RPM to raw values
    raw_velocity = int(velocity)
    print(f"Setting velocity to {raw_velocity}")
    dxl_comm_result, dxl_error = packetHandler.write4ByteTxRx(portHandler, DXL_ID, ADDR_GOAL_VELOCITY, raw_velocity)
    handle_write_confirmation(dxl_comm_result, dxl_error)

def read_current():
    """Get the present current of the motor"""

    # Read present current
    dxl_present_current, dxl_comm_result, dxl_error = packetHandler.read2ByteTxRx(portHandler, DXL_ID, ADDR_PRESENT_CURRENT)
    if dxl_comm_result != COMM_SUCCESS:
        print("%s" % packetHandler.getTxRxResult(dxl_comm_result))
    elif dxl_error != 0:
        print("%s" % packetHandler.getRxPacketError(dxl_error))

    return dxl_present_current

def main():
    if not setup_dynamixel():
        print("Failed to setup Dynamixel")
        return

    print("\nMotor Control Ready!")
    print("Commands:")
    print("f: Forward | b: Backward | s: Stop | q: Quit")
    print("1-9: Adjust speed (10%-90%)")
    print("\nMonitoring started...\n")

    speed_percentage = 50  # Default speed (50%)
    speed_percentage = 50  # Default speed
    direction = "Stopped"
    running = True
    last_cmd_time = time.time()

    while running:

        try:
            current_mA = read_current()
            current_time = time.time()

            # Only print status every 100ms to avoid flooding the terminal
            if current_time - last_cmd_time >= 0.1:
                print_status(speed_percentage, direction, current_mA)
                last_cmd_time = current_time

            cmd = input("\nEnter command: ").lower()

            if cmd == 'q':
                set_velocity(0)
                packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, 0)
                running = False

            elif cmd == 'f':
                velocity = -200 * (speed_percentage / 100)
                set_velocity(velocity)
                direction = "Forward"
                print("\nCommand: Forward")

            elif cmd == 'b':
                velocity = 200 * (speed_percentage / 100)
                set_velocity(velocity)
                direction = "Backward"
                print("\nCommand: Backward")

            elif cmd == 's':
                set_velocity(0)
                direction = "Stopped"
                print("\nCommand: Stop")

            elif cmd.isdigit() and 1 <= int(cmd) <= 9:
                speed_percentage = int(cmd) * 10
                print(f"\nSpeed set to {speed_percentage}%")

            portHandler.closePort()
            print("\nProgram terminated")

        except KeyboardInterrupt:
            print("\nEmergency stop!")
            set_velocity(0)
            packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, 0)
            break

    portHandler.closePort()

if __name__ == "__main__":
    main()
