from .conftest import run_script
from .conftest import skip_if_no_proc_tasks


pytestmark = [skip_if_no_proc_tasks]


def test_thread_title_unchanged():
    rv = run_script(
        """
from glob import glob

def print_stuff():
    for fn in sorted(glob("/proc/self/task/*/comm")):
        with open(fn) as f:
            print(f.readline().rstrip())

print_stuff()
print("---")
import setproctitle
print_stuff()
print("---")
print(setproctitle.getthreadtitle())
""",
    )
    before, after, gtt = rv.split('---\n')
    assert before == after
    assert before == gtt


def test_set_thread_title():
    run_script(
        """
from glob import glob
import setproctitle
setproctitle.setthreadtitle("hello" * 10)

(fn,) = glob("/proc/self/task/*/comm")
with open(fn) as f:
    assert f.read().rstrip() == "hello" * 3
""",
    )


def test_set_threads_title():
    run_script(
        """
import time
import threading
from glob import glob

(fn,) = glob("/proc/self/task/*/comm")
with open(fn) as f:
    orig = f.read().rstrip()

import setproctitle

def worker(title, ready):
    setproctitle.setthreadtitle(title)
    ready.set()
    while 1:
        time.sleep(1)

ready1 = threading.Event()
ready2 = threading.Event()
t1 = threading.Thread(target=worker, args=('reader', ready1), daemon=True)
t2 = threading.Thread(target=worker, args=('writer', ready2), daemon=True)
t1.start()
t2.start()

# Starting a thread does not guarantee that it has set its title yet.
assert ready1.wait(5), "reader did not become ready"
assert ready2.wait(5), "writer did not become ready"

comms = []
for fn in glob("/proc/self/task/*/comm"):
    with open(fn) as f:
        comms.append(f.read().rstrip())

comms.sort()
assert comms == sorted([orig, "reader", "writer"])
""",
    )
