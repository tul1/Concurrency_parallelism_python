from queue import Queue
from threading import Thread
import time

in_queue = Queue()

def consumer():
    print('Consumer waiting')
    work = in_queue.get()
    print('Consumer working')
    for _ in range(2):
        time.sleep(0.1)
        print(f'{work}')
    print('Consumer done')
    in_queue.task_done()


thread = Thread(target=consumer)
thread.start()

print('Producer putting')
in_queue.put('toto')
print('Producer waiting')
thread.join()
print('Producer done')
