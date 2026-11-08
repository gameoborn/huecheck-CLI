from huecheck.contrast import contrast_ratio, parse_hex
from huecheck.cvd import simulate
from huecheck.parser import parse_ansi


def test_wcag_contrast_known_values():
    assert contrast_ratio(parse_hex("#fff"), parse_hex("#000")) == 21
    assert round(contrast_ratio(parse_hex("#767676"), parse_hex("#fff")), 1) == 4.5


def test_parse_sgr_palette_truecolor_bold_reverse_and_reset():
    spans = parse_ansi(b"plain\x1b[1;31mred\x1b[38;5;200m pink\x1b[48;2;1;2;3;7m rev\x1b[0mend")
    assert spans[0].text == "plain"
    assert spans[1].bold and spans[1].foreground == ("ansi", 1)
    assert spans[2].foreground == ("rgb", (255, 0, 215))
    assert spans[3].reverse and spans[3].background == ("rgb", (1, 2, 3))
    assert spans[4].foreground is None and spans[4].text == "end"


def test_color_vision_transforms_are_bounded_and_distinct():
    for kind in ("protanopia", "deuteranopia", "tritanopia"):
        result = simulate((255, 0, 0), kind)
        assert all(0 <= channel <= 255 for channel in result)
        assert result != (255, 0, 0)
