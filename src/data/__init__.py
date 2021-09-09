from .data_handler import DataHandler


class Context(object):

    def __init__(self):
        self.data_handler = DataHandler()


ctx = Context()
