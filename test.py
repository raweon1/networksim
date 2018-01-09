from collections import deque


def next_package(max_priority, queues):
    for i in range(0, max_priority + 1):
        try:
            return queues[i].popleft()
        except IndexError:
            pass
    print(str(queues) + " h ")
    return None


queues = {1: deque([1, 2, 3]), 0: deque([])}

print(next_package(3, queues))
