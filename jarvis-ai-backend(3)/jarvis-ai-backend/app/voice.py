"""
Voice layer (Day 5).

Left provider-agnostic on purpose -- plug in whichever STT/TTS you land
on (e.g. Deepgram, AssemblyAI, or OpenAI Whisper for STT; ElevenLabs or
a browser-native SpeechSynthesis call from Khushi's frontend for TTS).
Wire the real API call inside these two functions only; nothing else
in the AI layer needs to change.
"""


async def transcribe_audio(audio_bytes: bytes) -> str:
    """Convert recorded audio into text. Replace body with your chosen
    STT provider's API call."""
    raise NotImplementedError(
        "Wire up an STT provider here (e.g. Whisper API, Deepgram). "
        "Input: raw audio bytes from the frontend's voice-command button. "
        "Output: transcribed command text."
    )


async def synthesize_speech(text: str) -> bytes:
    """Convert JARVIS's text response into speech audio bytes. Replace
    body with your chosen TTS provider's API call, OR skip this
    entirely and have Khushi's frontend use the browser's built-in
    SpeechSynthesis API on the text `result` field -- simplest path
    for a one-week prototype."""
    raise NotImplementedError(
        "Wire up a TTS provider here, or handle TTS client-side in React "
        "with the Web Speech API instead."
    )
