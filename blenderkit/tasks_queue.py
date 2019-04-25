import bpy

import queue

import blenderkit

tasks_queue = queue.Queue()

def every_2_seconds():
    while not tasks_queue.empty():
        print('as a task:   ')
        fstring = tasks_queue.get()
        eval(fstring)
    return 2.0

def register():
    bpy.app.timers.register(every_2_seconds)

def unregister():
    bpy.app.timers.unregister(every_2_seconds)