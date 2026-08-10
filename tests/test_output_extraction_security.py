from dr_output_extraction_v1 import extract_code, extract_integer
from llm_output_parsing import extract_json_object_from_text


def test_fenced_json_remains_preferred_over_earlier_plain_json():
    parsed, error = extract_json_object_from_text(
        '{"source":"plain"}\n```json\n{"source":"fenced"}\n```'
    )

    assert parsed == {"source": "fenced"}
    assert error is None


def test_invalid_first_fenced_json_keeps_plain_json_fallback_order():
    parsed, error = extract_json_object_from_text(
        '{"source":"plain"}\n```json\n{broken}\n```\n```json\n{"source":"later"}\n```'
    )

    assert parsed == {"source": "plain"}
    assert error is None


def test_json_extraction_handles_long_repeated_fence_and_brace_prefix():
    adversarial_prefix = "```{{" * 20_000

    parsed, error = extract_json_object_from_text(adversarial_prefix + '{"safe":true}')

    assert parsed == {"safe": True}
    assert error is None


def test_code_extraction_preserves_language_fence_behavior():
    code, ok, note = extract_code("before```PyThOn\nprint('safe')\n```after")

    assert code == "print('safe')"
    assert ok is True
    assert note == "first fenced code block"


def test_code_extraction_handles_long_unclosed_whitespace_fence():
    code, ok, note = extract_code("```" + (" " * 250_000))

    assert code == ""
    assert ok is False
    assert note == "no fenced block or plausible Python code found"


def test_integer_extraction_handles_many_labels_without_a_number():
    extracted, ok, note = extract_integer("final " * 50_000)

    assert extracted == ""
    assert ok is False
    assert note == "no integer found"


def test_integer_extraction_preserves_labeled_number_behavior():
    extracted, ok, note = extract_integer("analysis complete; final answer: 12,345")

    assert extracted == "12345"
    assert ok is True
    assert note == "extracted integer"


def test_integer_extraction_preserves_negative_labeled_number_behavior():
    extracted, ok, note = extract_integer("analysis complete; final: -12,345")

    assert extracted == "-12345"
    assert ok is True
    assert note == "extracted integer"
