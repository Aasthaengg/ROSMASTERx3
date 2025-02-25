import whisper

class WhisperSTT:
    def __init__(self, model_size: str = 'small', english: bool = True, translate: bool = False) -> None:
        self.english = english
        self.translate = translate
        print("\033[96mLoading Whisper Model..\033[0m", end='', flush=True)
        self.model = whisper.load_model(f'{model_size}')
        print("\033[90m Done.\033[0m")

    def inference(self) -> str:
        audio = whisper.load_audio('dictate.wav')
        audio = whisper.pad_or_trim(audio)

        mel = whisper.log_mel_spectrogram(audio).to(self.model.device)

        options = whisper.DecodingOptions(language='en' if self.english else '')
        result = whisper.decode(self.model, mel, options)
        return result.text