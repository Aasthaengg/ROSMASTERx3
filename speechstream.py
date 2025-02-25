import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write
from threading import Thread
from whisperstt import WhisperSTT
import time
import os


class StreamHandler:
    def __init__(
            self, 
            assist=None,
            samplerate: int = 44100,
            blocksize: int = 30,
            threshold: float = 0.1,
            vocals: tuple = [50, 1000],
            endblocks: int = 40,
            debug=False,
        ) -> None:
        self.debug = debug
        self.samplerate = samplerate
        self.blocksize = blocksize
        self.threshold = threshold
        self.vocals = vocals
        self.endblocks = endblocks
        self.running = True
        self.padding = 0
        self.prevblock = self.buffer = np.zeros((0,1))
        self.fileready = False
        self.whisper_stt = WhisperSTT()
        self.stt_result = None
        self.speaking = False

        t = Thread(target=self.listen)
        t.daemon = True
        t.start()


    def callback(self, indata, frames, t, status) -> None:
        if not any(indata) and self.debug:
            print('\033[31m.\033[0m', end='', flush=True) # if no input, prints red dots
            return

        freq = np.argmax(np.abs(np.fft.rfft(indata[:, 0]))) * self.samplerate / frames
        if np.sqrt(np.mean(indata**2)) > self.threshold and self.vocals[0] <= freq <= self.vocals[1]:
            self.speaking = True
            if self.debug:
                print('.', end='', flush=True)
            if self.padding < 1: self.buffer = self.prevblock.copy()
            self.buffer = np.concatenate((self.buffer, indata))
            self.padding = self.endblocks
        else:
            self.speaking = False
            self.padding -= 1
            if self.padding > 1:
                self.buffer = np.concatenate((self.buffer, indata))
            elif self.padding < 1 and self.buffer.shape[0] > (self.samplerate * 1):  # Ensure at least 1 second of audio
                self.fileready = True
                write('dictate.wav', self.samplerate, self.buffer) # I'd rather send data to Whisper directly..
                self.buffer = np.zeros((0,1))
            elif self.padding < 1 < self.buffer.shape[0] < self.samplerate: # if recording not long enough, reset buffer.
                self.buffer = np.zeros((0,1))
                print("\033[2K\033[0G", end='', flush=True)
            else:# Number of blocks to wait before sending to Whisper
                self.prevblock = indata.copy() #np.concatenate((self.prevblock[-int(self.samplerate/10):], indata)) # SLOW


    def process(self) -> None:
        if self.fileready:
            print("\n📂 File ready for transcription!")

            if not os.path.exists('dictate.wav'):
                print("❌ Error: dictate.wav was not created!")
                return
            
            print("📝 Transcribing...")
            result = self.whisper_stt.inference()
            if result.strip() == "":
                print("⚠️ Warning: Whisper returned an empty transcript!")
            else:
                print(f"✅ Transcription: {result}")

            self.stt_result = result
            self.fileready = False


    def listen(self) -> None:
        print("\033[32mListening.. \033[37m(Ctrl+C to Quit)\033[0m")
        with sd.InputStream(
            channels=1, 
            callback=self.callback, 
            blocksize=int(self.samplerate * self.blocksize / 1000), 
            samplerate=self.samplerate
        ):
            while self.running:
                self.process()
                time.sleep(0.1)  # Small delay to avoid CPU overuse

