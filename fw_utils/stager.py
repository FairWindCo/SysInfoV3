import datetime


class Stage:
    def __init__(self) -> None:
        super().__init__()
        self.start_time = datetime.datetime.now()
        self.warning = False
        self.finish_success = None
        self.work_time = None

    def set_warning(self):
        self.warning = True

    def set_error(self):
        self.finish_success = False

    def end_work(self, success: bool = True):
        if self.finish_success is None:
            self.finish_success = success
        else:
            self.finish_success &= success
        self.work_time = datetime.datetime.now() - self.start_time
