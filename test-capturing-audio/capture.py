import subprocess
import numpy as np
import threading
import time

def run_command(monitor_name):
    print("The monitor: ", monitor_name)
    command = [
        "parecord",
        f"--device={monitor_name}",
        "--format=s16le",
        "--rate=44100",
        "--file-format=raw",
        "--channels=2",
        "output.raw"
    ]

    subprocess.run(command)


def pick_monitor_source():
    """
    Lists all PulseAudio sources (including monitor sources),
    allows you to pick one by index, and returns its name.
    """
    result = subprocess.run(["pactl", "list", "short", "sources"],
                            capture_output=True, text=True, check=True)
    lines = result.stdout.strip().split("\n")
    if not lines:
        raise RuntimeError("No PulseAudio sources found.")

    print("Available PulseAudio sources:")
    for i, line in enumerate(lines):
        print(f"{i}: {line}")

    choice = input("Pick a source number: ")
    try:
        choice_index = int(choice)
        if not (0 <= choice_index < len(lines)):
            raise ValueError("Choice out of range.")
    except ValueError as e:
        raise RuntimeError(f"Invalid selection: {e}")

    parts = lines[choice_index].split()
    if len(parts) < 2:
        raise RuntimeError("Failed to parse source line.")
    source_name = parts[1]
    return source_name

def main():
    monitor_name = pick_monitor_source()
    print(f"Selected source: {monitor_name}")

    thread = threading.Thread(target=lambda: run_command(monitor_name), daemon=True)
    thread.start()

    with open("output.raw", "rb") as f:
        f.seek(0, 2)
        while True:
            print("Is this doing anything?")
            data = f.read(1024)  # Read new data
            if data:
                numpy_array = np.frombuffer(data, dtype=np.int16)
                print(numpy_array[:10])
            time.sleep(0.5)

if __name__ == "__main__":
    main()

