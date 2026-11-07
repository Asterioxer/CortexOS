from cortex.embodiment.streaming_tts import split_ready_sentences


def test_sentence_split_waits_for_boundary():
    ready, tail = split_ready_sentences("Hello there. How are")
    assert ready == ["Hello there."]
    assert tail == "How are"


def test_sentence_split_flushes_tail():
    ready, tail = split_ready_sentences("All done!", flush=True)
    assert ready == ["All done!"]
    assert tail == ""
