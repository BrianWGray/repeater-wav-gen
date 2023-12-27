#!/usr/bin/env python3

"""rpwavgen: Repeater WAV Generator

The repeater WAV generator is a tool for generating WAV files for use with
ICOM repeaters. It is designed to be used with the ICOM ID-RP4010V, ID-RP2010V,
and ID-RP1200VD repeaters, but may work with other ICOM repeaters as well.

The repeater WAV generator is a command line tool to generate WAV files for use
with ICOM repeaters. The generated WAV files are used to ID the repeater and
provide other audio messages to users.

Written for use on MacOS using Apple's NSSpeechSynthesizer class.

The data filename must be “Speech.wav.”
ID-RP3>Speech>Speech.wav
"""
import os
import argparse
import wave
import AppKit
import pydub
from pydub import AudioSegment

FILE_NAME = 'Speech.wav'
WAV_FORMAT = {'filename':FILE_NAME,
              'format':'wav',
              'max_length':10,
              'sampling_rate':16,
              'bit_rate':16,
              'channel':1,
              'modulation':'PCM'}
NARRATOR = 'com.apple.voice.enhanced.en-US.Allison'
RATE = 175


def parse_args():
    """Parse command line arguments."""

    parser = argparse.ArgumentParser(
        description="Repeater WAV Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="See")

    # define option groups
    wav_input_grp = parser.add_mutually_exclusive_group()
    wav_convert_grp = parser.add_mutually_exclusive_group()

    # define options
    wav_input_grp.add_argument("-t", "--text",
                               help="Text to convert to WAV file")
    wav_input_grp.add_argument("-i", "--input",
                               help="Input WAV file to convert or validate")

    wav_convert_grp.add_argument("-c", "--convert",
                                action="store_true",
                                help="Convert a WAV file to proper format")
    wav_convert_grp.add_argument("-v", "--validate",
                                action="store_true",
                                help="Validate a WAV file")

    parser.add_argument("-o", "--output",
                        help="Output WAV file directory location",
                        default=".")
    parser.add_argument("-g", "--gain",
                        type=check_gain,
                        help="Gain of WAV file",
                        default=1)
    parser.add_argument("-r", "--rate",
                        help="Rate of WAV file",
                        type=int,
                        choices=range(1,300),
                        default=RATE)
    parser.add_argument("-n", "--narrator",
                        help="Narator of WAV file",
                        choices=list_voices(),
                        default=NARRATOR)

    return parser.parse_args()


def check_gain(value) -> float:
    """
    Check gain value.

    Args:
        value: Gain value to check.

    Returns:
        Gain value if valid.
    """

    try:
        # Try to convert the value to a float
        fvalue = float(value)
    except ValueError as exc:
        # Raise argparse error if conversion fails
        raise argparse.ArgumentTypeError(f"{value} is an invalid gain value. Use a float.") from exc

    # Check if the value is in the specified range
    if 0.01 <= fvalue <= 1.0:
        return fvalue
    else:
        raise argparse.ArgumentTypeError("Gain must be between 0.01 and 1.0")


def validate_wav_mod(file_name: str) -> bool:
    """
    Validate WAV file modulation.

    Args:
        file_name: Name of WAV file to validate.

    Returns:
        True if file is PCM, False otherwise.
    """

    # Open the file with wave module
    with wave.open(file_name, 'rb') as wav_file:
        # Acquire file parameters
        sample_width = wav_file.getsampwidth()
        frame_rate = wav_file.getframerate()
        n_channels = wav_file.getnchannels()
        n_frames = wav_file.getnframes()
        comp_type = wav_file.getcomptype()

        print("Sample Width:", (sample_width*8))
        print("Frame Rate (Hz):", frame_rate)
        print("Number of Channels:", n_channels)
        print("Number of Frames:", n_frames)
        print("Compression Type:", comp_type)

    # Determine if the compression type is PCM
    if comp_type == 'NONE':
        print("This is likely a PCM file.")
        return True
    else:
        print("This file might not be PCM.")
        return False


def validate_wav(file_name:str=FILE_NAME, wav_format:dict=WAV_FORMAT) -> bool:
    """
    Validate WAV file format.

    file requirements:
        File name: Speech.wav
        File format: wav
        Max Length: 10 seconds
        Sampling Rate: 16kHz
        Bit Rate: 16bit
        Channel: Mono
        Modulation: PCM

    Returns:
        True if file is valid, False otherwise.
    """

    # validate WAV file format
    wav_file = pydub.AudioSegment.from_file(file_name)

    bit_rate = wav_format['bit_rate'] * 1000
    sampling_rate = wav_format['sampling_rate'] / 8

    if validate_wav_mod(file_name):
        file_modulation = 'PCM'
    else:
        file_modulation = 'Not PCM'

    if wav_file.duration_seconds > wav_format['max_length']:
        print(f"File is too long [{wav_file.duration_seconds} > {wav_format['max_length']}]")
        return False
    if wav_file.frame_rate != (bit_rate):
        print(f"File has wrong bit rate [{wav_file.frame_rate} != {bit_rate}]")
        return False
    # sample_width (int): Sample width in bytes (1=8-bit, 2=16-bit, 4=32-bit)
    if wav_file.sample_width != (sampling_rate):
        print(f"File has wrong sampling rate [{wav_file.sample_width} != {sampling_rate}]")
        return False
    if wav_file.channels != wav_format['channel']:
        print(f"File has wrong channel count[{wav_file.channels} != {wav_format['channel']}]")
        return False
    if file_modulation != wav_format['modulation']:
        print(f"File has wrong modulation type [{file_modulation} != {wav_format['modulation']}]")
        return False

    # return True if file is valid
    return True


def remove_file(file_name:str) -> None:
    """
    Remove a file.

    Args:
        file_name: Name of file to remove.

    Returns:
        None
    """

    # remove file
    try:
        os.remove(file_name)
    except OSError as exc:
        message = f"Unable to remove file: {file_name} ({exc})"
        raise OSError(message) from exc


def generate_wav(pargs, wav_format=WAV_FORMAT) -> None:
    """
    Generate WAV file from text.

    Args:
        pargs: Command line arguments.
        gain: Gain of WAV file.
        wav_format: Format of WAV file.
        narrator: Narrator of WAV file.
    """
    temp_speech = 'temp_speech.aiff'

    text_to_speech(pargs.text, temp_speech, gain=pargs.gain, rate=pargs.rate)
    convert_to_wav(temp_speech, f"{pargs.output}/{FILE_NAME}")
    remove_file(f"{pargs.output}/{temp_speech}")
    validate_wav(f"{pargs.output}/{FILE_NAME}")


def convert_to_wav(
    input_file: str,
    output_file: str,
    codec: str = "pcm_s16le",
    bitrate: str = "16k",
    channels: int = 1,
    sample_width: int = 2,
    frame_rate: int = 16000,
) -> None:
    """
    Convert an audio file to WAV format with pydub.

    Args:
        input_file (str): Path to the input file.
        output_file (str): Path to the output WAV file.
        codec (str): Codec to use for the output file.
        bitrate (str): Bitrate for the output file.
        sample_width (int): Sample width in bytes (1=8-bit, 2=16-bit, 4=32-bit).
        frame_rate (int): Frame rate or sample rate (in Hz).
        channels (int): Number of audio channels (1 for mono, 2 for stereo).

    """

    sound = AudioSegment.from_file(input_file)
    sound = sound.set_frame_rate(frame_rate)
    sound = sound.set_sample_width(sample_width)
    sound = sound.set_channels(channels)

    sound.export(output_file, format="wav", codec=codec, bitrate=bitrate)


def list_voices():
    """List available voices."""
    voices = AppKit.NSSpeechSynthesizer.availableVoices()
    return [str(voice) for voice in voices]


# Function to handle text-to-speech
def text_to_speech(
    text: str,
    output_file: str = FILE_NAME,
    narrator=NARRATOR,
    gain=None,
    rate=None
) -> None:
    """
    Convert text to speech.

    Args:
        text: Text to convert to speech.
        output_file: Output file to save speech to.
        voice_id: Voice to use for speech.
        volume: Volume to use for speech.
        rate: Rate to use for speech.

    Returns:
        None
    """

    if not narrator in list_voices():
        message = f"Invalid narrator: {narrator}"
        raise ValueError(message)

    # create speech synthesizer
    speech = AppKit.NSSpeechSynthesizer.alloc().initWithVoice_(narrator)

    # set speech volume
    if gain:
        speech.setVolume_(gain)

    # set speech rate
    if rate:
        speech.setRate_(rate)

    # create speech file
    speech.startSpeakingString_toURL_(text, AppKit.NSURL.fileURLWithPath_(output_file))

    # wait for speech to complete
    while speech.isSpeaking():
        pass

    # release speech synthesizer
    speech.release()


def main():
    """Main program entry point."""

    pargs = parse_args()

    if pargs.text:
        generate_wav(pargs)
    elif pargs.input and pargs.validate:
        validate_wav(pargs.input)
    elif pargs.input and pargs.convert:
        convert_to_wav(pargs.input, f"{pargs.output}/{FILE_NAME}")
    else:
        print("Invalid options")

if __name__ == "__main__":
    main()
