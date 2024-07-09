import pytest

from SYNKABOT.main import image_check, print_secret, regex_check

LIST_OF_GOOD_STRINGS = ["",
                        "||a||"
                        "||a||\n||a||"
                        ]
LIST_OF_BAD_STRINGS = ["||||",
                       "||a||\na",
                       "||a||a",
                       "||a",
                       "abc||def",
                       "|abc||",
                       "||abc|",
                       "|abc|"]


class MockAttachment():
    def __init__(self, input_string) -> None:
        self.filename = input_string


GOOD_MAs = [
    MockAttachment("SPOILER_1.png"),
    MockAttachment("SPOILER_dsthdrt.png"),
    MockAttachment("SPOILER_dasrgye56yw4536t.png"),
    MockAttachment("SPOILER_548764u.jpg"),
    MockAttachment("SPOILER_rs7redged.bmp")
]


BAD_MAs = [
    MockAttachment("SPOIsdagLER_1.png"),
    MockAttachment("SPOsdfILER_dsthdrt.png"),
    MockAttachment("SPOasgdgasILER_dasrgye56yw4536t.png"),
    MockAttachment("SPOasdgILER_548764u.jpg"),
    MockAttachment("SPOgasdILER_rs7redged.bmp")
]


@pytest.mark.unit
def test_regex():
    for test_string in LIST_OF_GOOD_STRINGS:
        assert regex_check(test_string)
    for test_string in LIST_OF_BAD_STRINGS:
        assert not regex_check(test_string)


@pytest.mark.unit
def test_image():
    assert image_check([])
    assert image_check(GOOD_MAs)
    assert not image_check(BAD_MAs)
    assert not image_check(GOOD_MAs + [BAD_MAs[0]])


@pytest.mark.unit
def test_print_secret():
    """Checks that print_secret returns a hash value."""
    secret_int = 165843841834  # nosec
    secret_string = "lsearokghqrakesldlkerua"  # nosec
    encoded_int = print_secret(secret_int)
    encoded_string = print_secret(secret_string)
    assert isinstance(encoded_int, str)
    assert isinstance(encoded_string, str)
    assert secret_int != encoded_int
    assert secret_string != encoded_string

    class Unstringifyable:
        def __str__(self):
            raise TypeError("Can not by stringified")

    a = Unstringifyable()
    random_float = print_secret(a)
    assert isinstance(random_float, float)
