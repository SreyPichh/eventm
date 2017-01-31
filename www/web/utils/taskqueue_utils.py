from google.appengine.api.taskqueue.taskqueue import Task

def is_a_task(obj):
    return isinstance(obj, Task)
