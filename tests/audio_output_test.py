from piperscribe.settings import AppSettings


def test_audio_output_dir_round_trips_through_settings():
    original = AppSettings(audio_output_dir="/data/audiobooks")
    restored = AppSettings.from_dict(original.to_dict())
    assert restored.audio_output_dir == "/data/audiobooks"


def test_audio_output_dir_defaults_to_empty():
    assert AppSettings.from_dict({}).audio_output_dir == ""
