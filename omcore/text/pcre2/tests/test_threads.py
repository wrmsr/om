import threading

from .. import _pcre2 as pcre2
from .spans import find_spans


##


def test_code_is_shared_between_threads():
    code = pcre2.compile(rb'\p{L}+|\p{N}+|\s+|.', pcre2.UTF | pcre2.UCP)
    subjects = [
        'short héllo 123'.encode(),
        'long enough to be matched off the interpreter, wörld 456 '.encode() * 200,
    ]
    expected = [find_spans(code, subject) for subject in subjects]

    num_threads = 8
    barrier = threading.Barrier(num_threads)
    results: list = [None] * num_threads

    def run(i):
        barrier.wait()
        results[i] = [[find_spans(code, subject) for subject in subjects] for _ in range(5)]

    threads = [threading.Thread(target=run, args=(i,)) for i in range(num_threads)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    for result in results:
        assert result == [expected] * 5
