import pyaudio
import numpy as np
import whisper
import torch
import wave
import time
import queue
import threading
import sys  # We'll use sys.stdout.write

model = whisper.load_model("medium")

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 48000
CHUNK_DURATION = 0.5
ACCUMULATE_DURATION = 10

audio = pyaudio.PyAudio()
stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

print("Listening...")

audio_queue = queue.Queue()
audio_buffer = np.array([], dtype=np.int16)

# We'll accumulate the entire translated text in this string.
translated_text_so_far = ""

def record_chunk():
	global audio_buffer
	frames = []
	num_frames = int(RATE / CHUNK * CHUNK_DURATION)
	for _ in range(num_frames):
		data = stream.read(CHUNK, exception_on_overflow=False)
		frames.append(np.frombuffer(data, dtype=np.int16))

	audio_chunk = np.concatenate(frames, axis=0)
	audio_queue.put(audio_chunk)

def transcribe_audio():
	global audio_buffer, translated_text_so_far

	while True:
		chunk = audio_queue.get()

		audio_buffer = np.concatenate((audio_buffer, chunk), axis=0)
		max_samples = int(ACCUMULATE_DURATION * RATE)
		if len(audio_buffer) > max_samples:
			audio_buffer = audio_buffer[-max_samples:]

		# Skip transcription if silent
		if np.max(np.abs(audio_buffer)) < 500:
			continue

		with wave.open("temp_audio.wav", 'wb') as wf:
			wf.setnchannels(CHANNELS)
			wf.setsampwidth(audio.get_sample_size(FORMAT))
			wf.setframerate(RATE)
			wf.writeframes(audio_buffer.tobytes())

		result = model.transcribe(
			"temp_audio.wav",
			temperature=0,
			fp16=torch.cuda.is_available(),
			task="translate",
			no_speech_threshold=0.7,
			logprob_threshold=-1.0
		)

		recognized_text = result['text'].strip()
		if recognized_text:
			translated_text_so_far = recognized_text

			sys.stdout.write("\r" + " " * 10000)  # Overwrite old text with spaces
			sys.stdout.flush()
			sys.stdout.write("\r" + translated_text_so_far)
			sys.stdout.flush()


transcription_thread = threading.Thread(target=transcribe_audio, daemon=True)
transcription_thread.start()

while True:
	record_chunk()

