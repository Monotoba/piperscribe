from piperscribe.hidpi import clamp_size_to_available


def test_normal_window_unchanged_on_large_screen():
    assert clamp_size_to_available(1100, 750, 1920, 1080) == (1100, 750)


def test_huge_window_clamped_inside_large_screen():
    width, height = clamp_size_to_available(3000, 2000, 1920, 1080)
    assert width <= int(1920 * 0.92)
    assert height <= int(1080 * 0.90)


def test_too_small_window_grows_to_minimum():
    assert clamp_size_to_available(300, 200, 1920, 1080) == (760, 520)


def test_double_size_window_on_1920x1080_clamps_to_ratio():
    width, height = clamp_size_to_available(3840, 2160, 1920, 1080)
    assert width <= 1920 * 0.92
    assert height <= 1080 * 0.90


def test_minimum_never_exceeds_available_area():
    width, height = clamp_size_to_available(100, 100, 800, 600)
    assert width <= int(800 * 0.92)
    assert height <= int(600 * 0.90)


def test_small_screen_1024x768_is_sensible():
    width, height = clamp_size_to_available(1100, 750, 1024, 768)
    assert width == int(1024 * 0.92)
    assert height == int(768 * 0.90)
    assert width >= 760
    assert height >= 520
