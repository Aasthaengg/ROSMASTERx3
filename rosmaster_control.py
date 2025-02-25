#!/usr/bin/env python3
# coding: utf-8

import socket
import time

class BotController:
    """
    A class-based controller for your bot. 
    Provides connection handling, directional sends, and preset routines.
    """

    def __init__(self, bot_ip="192.168.0.3", tcp_port=6000):
        """
        Initialize the BotController with default IP and port.
        """
        self.bot_ip = bot_ip
        self.tcp_port = tcp_port
        self.socket = None

    def connect(self):
        """Create a TCP socket and connect to the bot."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.bot_ip, self.tcp_port))
        print(f"[INFO] Connected to bot at {self.bot_ip}:{self.tcp_port}")

    def disconnect(self):
        """Close the socket connection."""
        if self.socket:
            self.socket.close()
            self.socket = None
            print("[INFO] Disconnected from bot.")

    @staticmethod
    def _calc_checksum(values):
        s = sum(values) & 0xFF
        return f"{s:02X}"

    @staticmethod
    def _build_btn_control(car_type_hex, num_dir_hex):
        cmd = 0x15
        length = 0x04
        to_sum = [car_type_hex, cmd, length, num_dir_hex]
        chksum = BotController._calc_checksum(to_sum)

        car_type_str = f"{car_type_hex:02X}"
        cmd_str      = f"{cmd:02X}"
        length_str   = f"{length:02X}"
        num_dir_str  = f"{num_dir_hex:02X}"

        packet = f"${car_type_str}{cmd_str}{length_str}{num_dir_str}{chksum}#"
        return packet

    def send_direction(self, direction, duration=1.0):
        """
        Sends a single 'direction' command (0..1) to the bot, 
        waits 'duration' seconds, then sends STOP.

        direction mapping in parse_data() => 
          0 = STOP,
          1 = FORWARD,
          2 = BACKWARD,
          3 = LEFT,
          4 = RIGHT,
          5 = ROTATE LEFT,
          6 = ROTATE RIGHT
        """
        if not self.socket:
            print("[ERROR] Bot is not connected.")
            return
        
        # Move
        packet = self._build_btn_control(0x01, direction)
        self.socket.sendall(packet.encode())
        time.sleep(duration)

        # Stop
        stop_packet = self._build_btn_control(0x01, 0x00)
        self.socket.sendall(stop_packet.encode())
        time.sleep(0.2)  # small break

    def dance_routine(self):
        """
        Example 'dance' routine: 
        forward -> rotate left -> backward -> rotate right -> etc.
        """
        print("[CMD] DANCE routine start")
        self.send_direction(1, 1.0)  # forward 1s
        self.send_direction(5, 1.0)  # rotate left 1s
        self.send_direction(2, 1.0)  # backward 1s
        self.send_direction(6, 1.0)  # rotate right 1s
        self.send_direction(3, 0.5)  # left
        self.send_direction(4, 0.5)  # right
        print("[CMD] DANCE routine end")

    def drift_routine(self):
        """
        'Drift' routine: maybe short forward then a rotate to simulate drifting
        """
        print("[CMD] DRIFT routine start")
        self.send_direction(1, 0.5)  # forward quickly
        self.send_direction(5, 1.5)  # rotate left longer
        self.send_direction(1, 0.5)  # forward again
        self.send_direction(6, 1.5)  # rotate right
        print("[CMD] DRIFT routine end")

    def circle_routine(self):
        """
        'Circle' routine: turn the bot in a circle.
        (If your bot can go forward + slight turn, adapt accordingly.)
        """
        print("[CMD] CIRCLE routine start")
        self.send_direction(5, 6.0)  # rotate left for 6 seconds
        print("[CMD] CIRCLE routine end")

    def square_routine(self):
        """
        'Square' routine: move forward, turn, do 4 edges
        """
        print("[CMD] SQUARE routine start")
        for _ in range(4):
            self.send_direction(1, 1.0)  # forward 1 second
            self.send_direction(5, 0.8)  # rotate left 0.8 second
        print("[CMD] SQUARE routine end")

    def triangle_routine(self):
        """
        'Triangle' routine: 3 edges
        """
        print("[CMD] TRIANGLE routine start")
        for _ in range(3):
            self.send_direction(1, 1.0)  # forward
            self.send_direction(5, 1.0)  # rotate left
        print("[CMD] TRIANGLE routine end")


# Example usage (you can comment this out if you only want the class definition):
if __name__ == "__main__":
    controller = BotController(bot_ip="192.168.0.3", tcp_port=6000)
    controller.connect()
    controller.dance_routine()
    controller.disconnect()
