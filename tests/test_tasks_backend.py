from bustag.app.tasks import InMemoryTaskQueue, create_task_queue, create_task_queue_from_env


def test_create_task_queue_memory_backend():
    queue = create_task_queue('memory', max_workers=1)
    assert isinstance(queue, InMemoryTaskQueue)
    assert queue.backend_name == 'memory'


def test_create_task_queue_unknown_fallback_to_memory():
    queue = create_task_queue('rq', max_workers=1)
    assert isinstance(queue, InMemoryTaskQueue)
    assert queue.backend_name == 'memory'


def test_create_task_queue_from_env(monkeypatch):
    monkeypatch.setenv('BUSTAG_TASK_BACKEND', 'memory')
    monkeypatch.setenv('BUSTAG_TASK_WORKERS', '1')
    queue = create_task_queue_from_env()
    assert isinstance(queue, InMemoryTaskQueue)
    assert queue.backend_name == 'memory'
