# from Queue import Queue
import threading
from Queue import Queue
from multiprocessing import Process, JoinableQueue
from threading import Thread
from time import sleep

from .logger import logger


class Worker(Thread):
    """Thread executing tasks from a given tasks queue"""

    def __init__(self, tasks, event):
        Thread.__init__(self)
        self.is_finish = True
        self.tasks = tasks
        self.daemon = True
        self.stopped = False
        self.event = event
        self.start()

    def run(self):
        while True and not self.stopped:
            data = self.tasks.get()
            try:
                if data is not None:
                    func, args, kargs = data
                    self.is_finish = False
                    func(*args, **kargs)
                    self.is_finish = True
            except Exception as err:
                logger.error(("Thread pool worker run error: " + str(err.message)), plugin="Thread pool")
                self.is_finish = True
                # raise
            finally:
                self.tasks.task_done()

    def is_finish(self):
        return self.is_finish

    def stop(self):
        # self.__block.acquire()
        self.stopped = True
        # self.__block.notify_all()
        # self.__block.release()

class MyThreadPool:
    """Pool of threads consuming tasks from a queue"""

    def __init__(self, num_threads):
        self.tasks = Queue(num_threads)
        self.event = threading.Event()
        self.threads = []
        for _ in range(num_threads):
            self.threads.append(Worker(self.tasks, self.event))
            sleep(0.1)

    def add_task(self, func, *args, **kargs):
        """Add a task to the queue"""
        self.tasks.put((func, args, kargs))

    def wait_completion(self):
        """Wait for completion of all the tasks in the queue"""
        self.tasks.join()

    def is_finish_all(self):
        for thread in self.threads:
            if not thread.is_finish:
                return False
        return True

    def stop(self):
        # self.wait_completion()
        for thread in self.threads:
            thread.stop()
        # for thread in enumerate():
        #     if thread.isAlive():
        #         try:
        #             thread._Thread__stop()
        #         except:
        #             print(str(thread.getName()) + ' could not be terminated'))


class WorkerProcess(Process):
    """Thread executing tasks from a given tasks queue"""

    def __init__(self, tasks):
        super(WorkerProcess, self).__init__()
        self.tasks = tasks

    def run(self):
        while True:
            data = self.tasks.get()
            try:
                if data is not None:
                    func, args, kargs = data
                    func(*args, **kargs)
            except Exception as err:
                logger.error(("Multi Process worker run error: " + str(err.message)), plugin="Multi Process")
                # raise
            finally:
                self.tasks.task_done()


class MyProcessPool:
    """Pool of Process consuming tasks from a queue"""

    def __init__(self, num_threads):
        self.tasks = JoinableQueue(num_threads)
        for _ in range(num_threads):
            WorkerProcess(self.tasks).start()

    def add_task(self, func, *args, **kargs):
        """Add a task to the queue"""
        self.tasks.put((func, args, kargs))

    def wait_completion(self):
        """Wait for completion of all the tasks in the queue"""
        self.tasks.join()
