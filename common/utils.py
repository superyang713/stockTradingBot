import logging
import os
import csv
import queue


class finishableQueue:

    def __init__(self, queue_to_finish):

        self._queue = queue_to_finish
        self.status = None

    def get(self, timeout):
        """
        Returns a list of queue elements once timeout is finished,
        or a FINISHED flag is received in the queue

        Params:
            timeout: how long to wait before giving up

        Return
            list of queue elements
        """
        contents_of_queue = []
        finished = False

        while not finished:
            try:
                current_element = self._queue.get(timeout=timeout)
                if current_element is None:
                    finished = True
                    self.status = None
                else:
                    contents_of_queue.append(current_element)
                    # keep going and try and get more data

            except queue.Empty:
                # If we hit a time out it's most probable we're not
                # getting a finished element any time soon give up
                # and return what we have
                finished = True
                self.status = None

        return contents_of_queue

    def timed_out(self):
        return self.status is None


def setup_log(name, usage=None):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if usage == "local":
        handler = logging.StreamHandler()
        formatter = logging.Formatter("[%(levelname)s] %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False

    return logger


# def get_historical_data(app: IBApp):

def write_historical_data__to_csv(filename, data: list):
    csv_file_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), filename,
    )
    fieldnames = ["Date", "Open", "High", "Low", "Close", "Volume"]
    with open(csv_file_path, "w") as fout:
        writer = csv.DictWriter(fout, fieldnames=fieldnames)
        writer.writeheader()
        for record in data:
            writer.writerow(dict(zip(fieldnames, record)))

