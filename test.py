import cv2
import requests
import numpy as np

# URL of the video feed from the Flask server
VIDEO_URL = "http://192.168.0.3:6500/video_feed"  # Replace <SERVER_IP> with the actual IP


def get_video_stream(url):
    """Fetch video stream from the Flask server."""
    try:
        cap = requests.get(url, stream=True)
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
                    cv2.imshow("Camera Feed", img)
                    if cv2.waitKey(1) == 27:  # Press 'ESC' to exit
                        break
        cap.close()
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to video stream: {e}")
    finally:
        cv2.destroyAllWindows()

if __name__ == "__main__":
    get_video_stream(VIDEO_URL)
