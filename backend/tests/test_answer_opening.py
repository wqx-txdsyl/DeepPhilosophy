"""A live comparison exposed blank answer chunks before the first paragraph."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from deep_streaming import AnswerEnvelopeParser, complete_paragraph_prefix


def test_answer_opening_blank_chunks_do_not_crash_paragraph_delivery():
    parser = AnswerEnvelopeParser()
    pending = ''
    for chunk in ['<answer>', '\n', '\n', ' ', '\n\n']:
        pending += parser.push(chunk)
        assert complete_paragraph_prefix(pending) == ''
    pending += parser.push('双方的核心分歧。\n\n下一段')
    assert complete_paragraph_prefix(pending).endswith('双方的核心分歧。\n\n')
