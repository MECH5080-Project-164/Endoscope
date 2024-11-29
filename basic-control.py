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

def setup_dynamixel():
    # Open port
    if portHandler.openPort():
        print("Succeeded to open the port")
    else:
        print("Failed to open the port")
        return False


    # Set port baudrate
    if portHandler.setBaudRate(BAUDRATE):
        print("Succeeded to change the baudrate")
    else:
        print("Failed to change the baudrate")
        return False

    # Disable torque to change operating mode
    dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, 0)
    handle_write_confirmation(dxl_comm_result, dxl_error)

    # Set operating mode to velocity control
    dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_OPERATING_MODE, VELOCITY_CONTROL_MODE)
    handle_write_confirmation(dxl_comm_result, dxl_error)

    # Enable torque
    dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, 1)
    handle_write_confirmation(dxl_comm_result, dxl_error)

    return True

def get_velocity_limit():
    """Get velocity limit of motor"""

    # Read present velocity
    dxl_present_velocity, dxl_comm_result, dxl_error = packetHandler.read4ByteTxRx(portHandler, DXL_ID, ADDR_VELOCITY_LIMIT)
    if dxl_comm_result != COMM_SUCCESS:
        print("%s" % packetHandler.getTxRxResult(dxl_comm_result))
    elif dxl_error != 0:
        print("%s" % packetHandler.getRxPacketError(dxl_error))

    return dxl_present_velocity

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
    print("f: Move forward")
    print("b: Move backward")
    print("s: Stop")
    print("q: Quit")
    print("\nUse numbers 1-9 to adjust speed (1=10%, 9=90%)")

    speed_percentage = 50  # Default speed (50%)

    while True:
        try:
            cmd = input("\nEnter command: ").lower()

            if cmd == 'q':
                # Stop motor and disable torque before quitting
                set_velocity(0)
                packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, 0)
                break

            elif cmd == 'b':
                velocity = 200 * (speed_percentage / 100)  # Convert percentage to actual velocity
                set_velocity(velocity)
                print(f"Moving forward at {speed_percentage}% speed")

            elif cmd == 'f':
                velocity = -200 * (speed_percentage / 100)  # Negative for backward movement
                set_velocity(velocity)
                print(f"Moving backward at {speed_percentage}% speed")

            elif cmd == 's':
                set_velocity(0)
                print("Stopped")

            elif cmd.isdigit() and 1 <= int(cmd) <= 9:
                speed_percentage = int(cmd) * 10
                print(f"Speed set to {speed_percentage}%")

            else:
                print("Invalid command")

        except KeyboardInterrupt:
            print("\nEmergency stop!")
            set_velocity(0)
            packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, 0)
            break

    portHandler.closePort()

if __name__ == "__main__":
    main()
