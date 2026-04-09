import time

from bustag.app.tasks import TaskQueue


def _wait_task_done(queue: TaskQueue, task_id: str, timeout: float = 2.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        task = queue.get(task_id)
        if task and task['status'] in {'success', 'failed'}:
            return task
        time.sleep(0.02)
    return queue.get(task_id)


def test_task_queue_success():
    queue = TaskQueue(max_workers=1)

    def add(a, b):
        return a + b

    task_id = queue.submit('add', add, 1, 2)
    task = _wait_task_done(queue, task_id)

    assert task is not None
    assert task['status'] == 'success'
    assert task['result'] == 3


def test_task_queue_failure():
    queue = TaskQueue(max_workers=1)

    def boom():
        raise RuntimeError('boom')

    task_id = queue.submit('boom', boom)
    task = _wait_task_done(queue, task_id)

    assert task is not None
    assert task['status'] == 'failed'
    assert 'boom' in task['error']
