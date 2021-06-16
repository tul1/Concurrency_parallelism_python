import time
import asyncio

ALIVE = '*'
EMPTY = '-'

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

async def game_logic(state, neighbors):
    # raise OSError('Problem with I/O')
    await asyncio.sleep(0.01)
    if state == ALIVE:
        if neighbors < 2:
            return EMPTY    # Die: Too few
        elif neighbors > 3:
            return EMPTY    # Die: Too many
    else:
        if neighbors == 3:
            return ALIVE    # Regenerate
    return state


async def step_cell(y, x, get, set):
    state = get(y,x)
    neighbors = count_neighbors(y, x, get)
    next_state = await game_logic(state, neighbors)
    set(y, x, next_state)

async def simulate_coroutine(grid):
    next_grid = Grid(grid.height, grid.width)

    tasks = []
    for y in range(grid.height):
        for x in range(grid.width):
            task = step_cell(y, x, grid.get, next_grid.set)
            tasks.append(task)

    await asyncio.gather(*tasks)

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
for _ in range(10):
    columns.append(str(grid))
    grid = asyncio.run(simulate_coroutine(grid))
end = time.time()
delta = end - start
print(f'Took {delta:.3f}')
print(columns)