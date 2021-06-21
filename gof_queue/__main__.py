from queue import Queue
from threading import Thread
import time

class ClosableQueue(Queue):
    SENTINEL = object()

    def close(self):
        self.put(self.SENTINEL)

    def __iter__(self):
        while True:
            item = self.get()
            try:
                if item is self.SENTINEL:
                    return
                yield item
            finally:
                self.task_done()


in_queue = ClosableQueue()
out_queue = ClosableQueue()

class StoppableWorker(Thread):
    def __init__(self, func, in_queue, out_queue):
        super().__init__()
        self.func = func
        self.in_queue = in_queue
        self.out_queue = out_queue

    def run(self):
        for item in self.in_queue:
            result = self.func(item)
            self.out_queue.put(result)

def game_logic(state, neighbors):
    time.sleep(0.01)
    # raise OSError('Problem with I/O')
    if state == ALIVE:
        if neighbors < 2:
            return EMPTY    # Die: Too few
        elif neighbors > 3:
            return EMPTY    # Die: Too many
    else:
        if neighbors == 3:
            return ALIVE    # Regenerate
    return state

def game_logic_thread(item):
    y, x, state, neighbors = item
    try:
        next_state = game_logic(state, neighbors)
    except Exception as e:
        next_state = e
    return (y, x, next_state)

# Start the threads upfront
threads = []
for _ in range(5):
    thread = StoppableWorker(game_logic_thread, in_queue, out_queue)
    thread.start()
    threads.append(thread)

ALIVE = '*'
EMPTY = '-'

class SimulationError(Exception):
    pass

class Grid:
    def __init__(self, height, width):
        self.height = height
        self.width = width
        self.rows = [[EMPTY] * self.width for _ in range(self.height)]

    def get(self, y, x):
        return self.rows[y % self.height][x % self.width]

    def set(self, y, x, state):
        self.rows[y % self.height][x % self.width] = state

    def __str__(self):
        return '\n'.join(map(lambda row: ''.join(row), self.rows))

def count_neighbors(y, x, get):
    n_ = get(y - 1, x + 0) # North
    ne = get(y - 1, x + 1) # Northeast
    e_ = get(y + 0, x + 1) # East
    se = get(y + 1, x + 1) # Southeast
    s_ = get(y + 1, x + 0) # South
    sw = get(y + 1, x - 1) # Southwest
    w_ = get(y + 0, x - 1) # West
    nw = get(y - 1, x - 1) # Northwest
    neighbor_state = [n_, ne, e_, se, s_, sw, w_, nw]
    count = len(list(filter(lambda x: x == ALIVE, neighbor_state)))
    return count

def simulate_pipeline(grid, in_queue, out_queue):
    for y in range(grid.height):
        for x in range(grid.width):
            state = grid.get(y, x)
            neighbors = count_neighbors(y, x, grid.get)
            in_queue.put((y, x, state, neighbors))
    
    in_queue.join()
    out_queue.close()

    next_grid = Grid(grid.height, grid.width)
    for item in out_queue:
        y, x, next_state = item
        if isinstance(next_state, Exception):
            raise SimulationError('Error has been raised')
        next_grid.set(y, x, next_state)

    return next_grid

class ColumnsPrinter(list):
    def __str__(self):
        rows = [row.split('\n') for row in self]
        output = [' | '.join(row) for row in zip(*rows)]
        col_len = len(rows[0])-1
        spacing = ''.join([' ']*col_len)
        headers = ' | '.join([f'{spacing}{index+1}{spacing}' for index in range(len(rows))])
        output.insert(0, headers)
        return '\n'.join(output)
     

grid = Grid(5, 9)
grid.set(0, 3, ALIVE)
grid.set(1, 4, ALIVE)
grid.set(2, 2, ALIVE)
grid.set(2, 3, ALIVE)
grid.set(2, 4, ALIVE)

columns = ColumnsPrinter()
start = time.time()
try:
    for _ in range(10):
        columns.append(str(grid))
        grid = simulate_pipeline(grid, in_queue, out_queue)
    end = time.time()
    delta = end - start
    print(f'Took {delta:.3f}')
    print(columns)
finally:
    for thread in threads:
        in_queue.close()
    for thread in threads:
        thread.join()