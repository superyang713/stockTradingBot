import logging
import os
import csv
import queue


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

