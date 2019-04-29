import bpy

import queue

from blenderkit import utils

def get_queue():
    if not hasattr(bpy.types.VIEW3D_PT_blenderkit_unified, 'task_queue'):
        bpy.types.VIEW3D_PT_blenderkit_unified.task_queue = queue.Queue()
    return bpy.types.VIEW3D_PT_blenderkit_unified.task_queue


def add_task(task):
    q = get_queue()
    q.put(task)


def every_2_seconds():
    q = get_queue()

    while not q.empty():
        utils.p('as a task:   ')
        q = bpy.types.VIEW3D_PT_blenderkit_unified.task_queue
        task = q.get()
        try:
            task[0](*task[1])
        except Exception as e:
            utils.p('task failed:')
            print(e)
    return 2.0


def register():
    bpy.app.timers.register(every_2_seconds)


def unregister():
    bpy.app.timers.unregister(every_2_seconds)
