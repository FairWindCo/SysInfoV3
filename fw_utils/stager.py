import datetime


class Stage:
    def __init__(self) -> None:
        super().__init__()
        self.stage_num = 0
        self.stage = {}
        self.start_time = datetime.datetime.now()

    def add_stage(self, message):
        self.stage_num = self.stage_num + 1
        self.stage[self.stage_num] = {
            'name': message,
            'start': datetime.datetime.now(),
            'warning': [],
            'result': None
        }

