#!/usr/bin/env python3
# coding: utf-8

import re
import time
import numpy as np
import cv2
import sounddevice as sd
from threading import Thread
import requests
import io

# Local imports (adjust paths as needed)
from speechstream import StreamHandler
from moondream import Moondream
from rosmaster_control import BotController
import pydub
import pydub.playback

# For demonstration, print available audio devices
print(sd.query_devices())

# Global references for storing recognized text commands and camera frame
global IMAGE, TEXT
IMAGE = None
TEXT = None


# URL of the video feed from the Flask server
VIDEO_URL = "http://192.168.0.3:6500/video_feed"  # Replace <SERVER_IP> with actual IP

DEEPGRAM_API_KEY = "df0e2bc942f5a0920dd853e6432bdf91055cca22"
DEEPGRAM_URL = "https://api.deepgram.com/v1/speak?model=aura-asteria-en"

def text_to_speech(text):
    """Convert text to speech using Deepgram's API and play the audio immediately."""
    try:
        print('TTS: ', text)
        headers = {
            "Authorization": f"Token {DEEPGRAM_API_KEY}",
            "Content-Type": "text/plain"
        }
        
        response = requests.post(DEEPGRAM_URL, headers=headers, data=text)
        response.raise_for_status()
        
        # Load MP3 audio and play it
        audio_data = io.BytesIO(response.content)
        audio = pydub.AudioSegment.from_file(audio_data, format="mp3")
        pydub.playback.play(audio)
        print('TTS Done!')
    except requests.exceptions.RequestException as e:
        print(f"Error generating speech: {e}")
        
def get_video_stream(url):
    """Fetch video stream from the Flask server."""
    try:
        cap = requests.get(url, stream=True, timeout=10)
        bytes_buffer = b''
        
        for chunk in cap.iter_content(chunk_size=1024):
            bytes_buffer += chunk
            a = bytes_buffer.find(b'\xff\xd8')  # Start of JPEG
            b = bytes_buffer.find(b'\xff\xd9')  # End of JPEG
            
            if a != -1 and b != -1:
                jpg = bytes_buffer[a:b+2]
                bytes_buffer = bytes_buffer[b+2:]
                img = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                
                if img is not None:
                    global IMAGE
                    IMAGE = img
                    cv2.imshow("Camera Feed", img)
                    if cv2.waitKey(1) == 27:  # Press 'ESC' to exit
                        break
        cap.close()
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to video stream: {e}")
    finally:
        cv2.destroyAllWindows()


def command_parser(cmd: str) -> dict:
    """
    Parses user input (transcribed text) and returns 
    a dictionary of recognized commands.
    """
    cmd = cmd.lower().strip()
    commands = {}

    # Vision-based triggers
    if any(word in cmd for word in ["describe", "explain"]):
        commands["caption"] = None 

    # VQA (Visual Question Answering)
    if re.search(r"\b(how|what|who|where|why)\b", cmd):
        commands["query"] = cmd  # entire question

    # Object Detection
    detect_match = re.search(r"detect\s+(\w+)", cmd)
    if detect_match:
        object_name = detect_match.group(1).strip()
        commands["detect"] = object_name
    elif "detect" in cmd:
        commands["detect"] = "face"

    # Pointing to Objects
    point_match = re.search(r"point to (.+)|show me (.+)", cmd)
    if point_match:
        object_name = point_match.group(1) or point_match.group(2)
        if object_name:
            commands["point"] = object_name.strip()

    # Bot movement commands
    if "dance" in cmd:
        commands["bot"] = "dance"
        text_to_speech("Woohoo! Time to bust some moves!")
    elif "drift" in cmd:
        commands["bot"] = "drift"
        text_to_speech("Hold tight! Watch me drift!")
    elif "circle" in cmd:
        commands["bot"] = "circle"
        text_to_speech("Here I go, spinning like a graceful ballerina!")
    elif "square" in cmd:
        commands["bot"] = "square"
        text_to_speech("Navigating in a perfect box!")
    elif "triangle" in cmd:
        commands["bot"] = "triangle"
        text_to_speech("Let me trace a perfect nachos!")

    # Simple directional commands
    if "move forward" in cmd or "go forward" in cmd:
        commands["bot"] = "forward"
        text_to_speech("Marching ahead fearlessly!")
    elif "move backward" in cmd or "back" in cmd:
        commands["bot"] = "backward"
        text_to_speech("Reversing with style!")
    elif "turn left" in cmd:
        commands["bot"] = "left"
        text_to_speech("Left is cool!")
    elif "turn right" in cmd:
        commands["bot"] = "right"
        text_to_speech("Right turn coming up!")
    elif "rotate left" in cmd:
        commands["bot"] = "rotate_left"
        text_to_speech("Spinning left like a pro!")
    elif "rotate right" in cmd:
        commands["bot"] = "rotate_right"
        text_to_speech("Here comes a smooth right spin!")
    elif "stop" in cmd:
        commands["bot"] = "stop"
        text_to_speech("Alright, stopping now!")

    return commands

def vision():
    """Continuously fetch and update frames."""
    while True:
        get_video_stream(VIDEO_URL)
        time.sleep(0.1)

# def vision(source=0):
#     """
#     Continuously reads frames from the specified source 
#     and updates the global IMAGE.
#     """
#     cap = cv2.VideoCapture(source)
#     if not cap.isOpened():
#         print(f"[ERROR] Could not open camera source {source}")
#         return

#     while True:
#         ret, frame = cap.read()
#         if not ret:
#             print("[WARNING] Empty frame received.")
#             continue
        
#         global IMAGE
#         IMAGE = frame

#         # Press 'q' to exit vision loop
#         if cv2.waitKey(1) & 0xFF == ord('q'):
#             break

#     cap.release()
#     cv2.destroyAllWindows()

def conversation(handler: StreamHandler):
    """
    Continuously checks for new speech recognition results
    and updates the global TEXT dictionary with recognized commands.
    """
    global TEXT

    while True:
        if handler.stt_result:
            # Retrieve the transcribed text
            user_input = handler.stt_result
            handler.stt_result = None
            
            print(f"\n[User] {user_input}")

            # Parse commands from the user input
            commands = command_parser(user_input)

            if commands:
                TEXT = commands
                print("[INFO] Commands detected:", TEXT)
            else:
                print("[INFO] No actionable command found.")
        time.sleep(0.05)

def main():
    global IMAGE, TEXT
    IMAGE = None
    TEXT = None

    # 1) Initialize the BotController
    bot = BotController(bot_ip="192.168.0.3", tcp_port=6000)
    try:
        bot.connect()
    except Exception as e:
        print(f"[ERROR] Failed to connect to bot: {e}")
        bot = None

    # 2) Initialize Whisper STT
    handler = StreamHandler()

    # 3) Initialize Vision logic (Moondream)
    moon = Moondream()

    # 4) Start Vision Thread
    vision_thread = Thread(target=vision)  # or any other video source
    vision_thread.daemon = True
    vision_thread.start()

    # 5) Start Conversation Thread
    conversation_thread = Thread(target=conversation, args=(handler,))
    conversation_thread.daemon = True
    conversation_thread.start()

    # 6) Main loop: process commands when TEXT is available
    try:
        while True:
            time.sleep(0.1)

            if TEXT is not None:
                # A) Handle BOT commands if a valid bot connection exists
                if bot and "bot" in TEXT:
                    cmd = TEXT["bot"]
                    if cmd == "dance":
                        bot.dance_routine()
                    elif cmd == "drift":
                        bot.drift_routine()
                    elif cmd == "circle":
                        bot.circle_routine()
                    elif cmd == "square":
                        bot.square_routine()
                    elif cmd == "triangle":
                        bot.triangle_routine()
                    elif cmd == "forward":
                        bot.send_direction(1, 0.5)
                    elif cmd == "backward":
                        bot.send_direction(2, 0.5)
                    elif cmd == "left":
                        bot.send_direction(3, 0.5)
                    elif cmd == "right":
                        bot.send_direction(4, 0.5)
                    elif cmd == "rotate_left":
                        bot.send_direction(5, 0.5)
                    elif cmd == "rotate_right":
                        bot.send_direction(6, 0.5)
                    elif cmd == "stop":
                        bot.send_direction(0, 0.2)

                # B) Handle Vision commands (if needed and if IMAGE is valid)
                if IMAGE is not None:
                    # Moondream processing as per your usage
                    results = moon.process_frame(IMAGE, TEXT)
                    try:
                        res = results[0][1]
                        print("[VISION] Results:", res)
                        text_to_speech(res)
                    except:
                        print(results)
                else:
                    print("[WARNING] IMAGE is not available yet.")

                # Clear TEXT after processing
                TEXT = None
    except KeyboardInterrupt:
        print("[INFO] Exiting app due to KeyboardInterrupt.")
    finally:
        # Ensure we clean up
        if bot:
            bot.disconnect()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
