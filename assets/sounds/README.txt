Drop your own .wav files in this folder.

Load them in main.py via:

    from game import sounds
    my_sound = sounds.load_wav("assets/sounds/your_file.wav")

Files are converted to mono and resampled to 44100 Hz automatically.
This folder is bundled into the standalone executable by yebin.spec.
