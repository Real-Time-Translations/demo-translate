import subprocess
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# Run 'pactl list sources' to find your monitor device
source_device = "bluez_output.64_5D_F4_E3_81_B9.1.monitor"  # Replace with your actual monitor source

# Start FFmpeg to capture system audio
command = [
    "ffmpeg", "-f", "pulse", "-i", source_device,
    "-ac", "2", "-ar", "44100",
    "-f", "f32le", "pipe:1"
]
process = subprocess.Popen(command, stdout=subprocess.PIPE, bufsize=4096)

# Audio settings
sample_rate = 44100
num_channels = 2
buffer_size = 1024  # Number of samples per update

# Initialize Matplotlib plot
fig, ax = plt.subplots()
x = np.arange(buffer_size)
y = np.zeros(buffer_size)
line, = ax.plot(x, y, color='blue')

ax.set_ylim(-1, 1)  # Audio amplitude range
ax.set_xlim(0, buffer_size)
ax.set_title("Real-Time System Audio Waveform")
ax.set_xlabel("Samples")
ax.set_ylabel("Amplitude")


def update(_):
    """Fetch new audio data and update the plot."""
    raw_audio = process.stdout.read(buffer_size * 4)

    if not raw_audio:
        return line,

    audio_data = np.frombuffer(raw_audio, dtype=np.float32)

    if num_channels == 2:
        audio_data = audio_data[::2]  # Take every second sample for one channel

    if len(audio_data) < buffer_size:
        audio_data = np.pad(audio_data, (0, buffer_size - len(audio_data)))

    line.set_ydata(audio_data)
    return line,


# Real-time animation
ani = animation.FuncAnimation(fig, update, interval=50, blit=True)

plt.show()

process.kill()  # Kill process when done

