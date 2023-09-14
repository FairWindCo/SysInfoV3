from dataclasses import dataclass
from datetime import datetime
from xml.etree import ElementTree as ET

import fw_isodurations

TASK_TRIGGER_EVENT = 0
TASK_TRIGGER_TIME = 1
TASK_TRIGGER_DAILY = 2
TASK_TRIGGER_WEEKLY = 3
TASK_TRIGGER_MONTHLY = 4
TASK_TRIGGER_MONTHLYDOW = 5
TASK_TRIGGER_IDLE = 6
TASK_TRIGGER_REGISTRATION = 7
TASK_TRIGGER_BOOT = 8
TASK_TRIGGER_LOGON = 9
TASK_TRIGGER_SESSION_STATE_CHANGE = 11
TASK_TRIGGER_CUSTOM_TRIGGER_01 = 12

TASK_CONSOLE_CONNECT = 1
TASK_CONSOLE_DISCONNECT = 2
TASK_REMOTE_CONNECT = 3
TASK_REMOTE_DISCONNECT = 4
TASK_SESSION_LOCK = 7
TASK_SESSION_UNLOCK = 8

STATE_CHANGES = {
    TASK_CONSOLE_CONNECT: 'CONSOLE_CONNECT',
    TASK_CONSOLE_DISCONNECT: 'CONSOLE_DISCONNECT',
    TASK_REMOTE_CONNECT: 'REMOTE_CONNECT',
    TASK_REMOTE_DISCONNECT: 'REMOTE_DISCONNECT',
    TASK_SESSION_LOCK: 'SESSION_LOCK',
    TASK_SESSION_UNLOCK: 'SESSION_UNLOCK',
}


def converting_date(date_str, formats=('%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%S%z')):
    if isinstance(formats, str):
        formats = (formats,)
    try:
        return datetime.fromisoformat(date_str)
    except ValueError:
        for format_str in formats:
            try:
                return datetime.strptime(date_str, format_str)
            except ValueError:
                print(date_str)
                pass
    raise ValueError('Incorrect Time Format')


@dataclass
class ITrigger:
    def __init__(self, trigger) -> None:
        super().__init__()
        self.is_enabled = trigger.Enabled
        self.type = trigger.Type
        self.start = trigger.StartBoundary
        self.end = trigger.EndBoundary
        self.id = trigger.Id

        self.stop_at_duration_and = trigger.Repetition.StopAtDurationEnd

        self.interval = fw_isodurations.parse_duration_ex(trigger.Repetition.Interval)
        self.duration = fw_isodurations.parse_duration_ex(trigger.Repetition.Duration)
        self.limit = fw_isodurations.parse_duration_ex(trigger.ExecutionTimeLimit)

        if self.start:
            self.start = fw_isodurations.parse_datetime(self.start)
        if self.end:
            self.end = fw_isodurations.parse_datetime(self.end)

    def get_trigger_type(self):
        if self.type == TASK_TRIGGER_EVENT:
            return 'EVENT'
        elif self.type == TASK_TRIGGER_BOOT:
            return 'BOOT'
        elif self.type == TASK_TRIGGER_IDLE:
            return 'IDLE'
        elif self.type == TASK_TRIGGER_TIME:
            return 'TIME'
        elif self.type == TASK_TRIGGER_LOGON:
            return 'LOGON'
        elif self.type == TASK_TRIGGER_DAILY:
            return 'DAILY'
        elif self.type == TASK_TRIGGER_WEEKLY:
            return 'WEEKLY'
        elif self.type == TASK_TRIGGER_MONTHLY:
            return 'MONTHLY'
        elif self.type == TASK_TRIGGER_MONTHLYDOW:
            return 'MONTHLYDOW'
        elif self.type == TASK_TRIGGER_REGISTRATION:
            return 'REGISTRATION'
        elif self.type == TASK_TRIGGER_SESSION_STATE_CHANGE:
            return 'SESSION_STATE_CHANGE'
        elif self.type == TASK_TRIGGER_CUSTOM_TRIGGER_01:
            return "CUSTOM_TRIGGER"
        else:
            return f'UNKNOWN({self.type})'

    @staticmethod
    def convert_date_str(date_str):
        return converting_date(date_str)

    @staticmethod
    def format_date(date: datetime):
        return date.strftime('%d-%m-%Y %H:%M:%S')

    def form_base_trigger_text(self):
        response = [self.get_trigger_type()]
        if self.start:
            response.append(f'Start: {self.format_date(self.start)}')
        if self.end:
            response.append(f'End: {self.format_date(self.end)}')
        if self.limit:
            response.append(f'Limit: {self.limit}')
        if self.duration or self.interval or self.stop_at_duration_and:
            response.append('(')
            if self.duration:
                response.append(f'Duration: {self.duration}')
            if self.interval:
                response.append(f'Interval: {self.interval}')
            if self.stop_at_duration_and:
                response.append(f'Stop At Duration End')
            response.append(')')
        return response

    def __str__(self) -> str:
        response = self.form_base_trigger_text()
        return ' '.join(response)

    def __repr__(self) -> str:
        return self.__str__()


class ITriggerTime(ITrigger):

    def __init__(self, trigger) -> None:
        super().__init__(trigger)
        self.random_delay = fw_isodurations.parse_duration_ex(trigger.RandomDelay)

    def form_base_trigger_text(self):
        response = super().form_base_trigger_text()
        if self.random_delay:
            response.append(f'RandomDelay: {self.random_delay}')
        return response


class IRegistrationTrigger(ITrigger):

    def __init__(self, trigger) -> None:
        super().__init__(trigger)
        self.delay = fw_isodurations.parse_duration_ex(trigger.Delay)

    def form_base_trigger_text(self):
        response = super().form_base_trigger_text()
        if self.delay:
            response.append(f'Delay: {self.delay}')
        return response


class ILogonTrigger(IRegistrationTrigger):

    def __init__(self, trigger) -> None:
        super().__init__(trigger)
        self.userID = trigger.UserId

    def form_base_trigger_text(self):
        response = super().form_base_trigger_text()
        if self.userID:
            response.append(f'User: {self.userID}')
        return response


class ITrigerDaily(ITrigger):

    def __init__(self, trigger) -> None:
        super().__init__(trigger)
        self.random_delay = fw_isodurations.parse_duration_ex(trigger.RandomDelay)

    def form_base_trigger_text(self):
        response = super().form_base_trigger_text()
        if self.random_delay:
            response.append(f'RandomDelay: {self.random_delay}')
        return response


class IMonth(ITriggerTime):
    MONTH_CODES = (
        ('Jun', 0x01),
        ('Feb', 0x02),
        ('Mar', 0x04),
        ('Apr', 0x08),
        ('May', 0x10),
        ('Jun', 0x20),
        ('Jul', 0x40),
        ('Aug', 0x80),
        ('Sep', 0x100),
        ('Oct', 0x200),
        ('Nov', 0x400),
        ('Dec', 0x800),
    )

    def __init__(self, trigger) -> None:
        super().__init__(trigger)
        self.month = trigger.MonthsOfYear

    def get_moth(self):
        return ','.join([name for name, code in self.MONTH_CODES if self.month & code])

    def form_base_trigger_text(self):
        response = super().form_base_trigger_text()
        if self.month:
            response.append(f'Month: [{self.get_moth()}]')
        return response


class ITriggerMonthly(IMonth):
    DAY_CODES = (
        (1, 0x01),
        (2, 0x02),
        (3, 0x04),
        (4, 0x08),
        (5, 0x10),
        (6, 0x20),
        (7, 0x40),
        (8, 0x80),
        (9, 0x100),
        (10, 0x200),
        (11, 0x400),
        (12, 0x800),
        (13, 0x1000),
        (14, 0x2000),
        (15, 0x4000),
        (16, 0x8000),
        (17, 0x10000),
        (18, 0x20000),
        (19, 0x40000),
        (20, 0x80000),
        (21, 0x100000),
        (22, 0x200000),
        (23, 0x400000),
        (24, 0x800000),
        (25, 0x1000000),
        (26, 0x2000000),
        (27, 0x4000000),
        (28, 0x8000000),
        (29, 0x10000000),
        (30, 0x20000000),
        (31, 0x40000000),
        (-1, 0x80000000),
    )

    def __init__(self, trigger) -> None:
        super().__init__(trigger)
        self.day = trigger.DaysOfMonth

    def get_days(self):
        return ','.join([str(day) for day, code in self.DAY_CODES if self.day & code])

    def form_base_trigger_text(self):
        response = super().form_base_trigger_text()
        if self.day:
            response.append(f'Days: [{self.get_days()}]')
        return response


class IDOW(ITrigger):
    DAY_CODES = (
        ('Sun', 0x01),
        ('Mon', 0x02),
        ('Tue', 0x04),
        ('Wed', 0x08),
        ('Thu', 0x10),
        ('Fry', 0x20),
        ('Sat', 0x40),
    )

    def __init__(self, trigger) -> None:
        super().__init__(trigger)
        self.day = trigger.DaysOfWeek

    def get_days(self):
        return ','.join([day for day, code in self.DAY_CODES if self.day & code])

    def form_base_trigger_text(self):
        response = super().form_base_trigger_text()
        if self.day:
            response.append(f'Days: [{self.get_days()}]')
        return response


class ITriggerDOW(IDOW, IMonth):
    def __init__(self, trigger) -> None:
        super().__init__(trigger)
        self.last_week_run = trigger.RunOnLastWeekOfMonth

    def form_base_trigger_text(self):
        response = super().form_base_trigger_text()
        if self.last_week_run:
            response.append(f' Run Last Month Week')
        return response


class IWeeklyTrigger(IDOW, ITriggerTime):
    def __init__(self, trigger) -> None:
        super().__init__(trigger)
        self.week_interval = trigger.WeeksInterval

    def form_base_trigger_text(self):
        response = super().form_base_trigger_text()
        if self.week_interval:
            response.append(f'Weeks: {self.week_interval}')
        return response


class IBootTrigger(IRegistrationTrigger):
    pass


class IEventTrigger(IBootTrigger):

    def __init__(self, trigger) -> None:
        super().__init__(trigger)
        self.subscription_xml = trigger.Subscription
        try:
            subscription = ET.fromstring(self.subscription_xml)

            self.subscription = [f'{path.attrib["Path"]}: {path.text}' for query in subscription.iterfind("Query") for
                                 path in
                                 query.iterfind('Select')]
        except ValueError:
            self.subscription = self.subscription_xml
        self.values = trigger.ValueQueries

    def form_base_trigger_text(self):
        response = super().form_base_trigger_text()
        if self.subscription:
            response.append(f'Subscription: {self.subscription}')
        if self.values:
            for value in self.values:
                response.append(f'search: {value}')

        return response


class IIdleTrigger(ITrigger):
    pass


class ISessionStateChangeTrigger(ILogonTrigger):

    def __init__(self, trigger) -> None:
        super().__init__(trigger)
        self.state_change = trigger.StateChange

    def state_change_desc(self):
        if self.state_change in STATE_CHANGES:
            return STATE_CHANGES[self.state_change]
        else:
            return self.state_change

    def form_base_trigger_text(self):
        response = super().form_base_trigger_text()
        if self.state_change:
            response.append(f'State Change: {self.state_change_desc()}')
        return response


class ICustomTrigger(ITrigger):

    def form_base_trigger_text(self):
        response = super().form_base_trigger_text()
        if self.id:
            response.append(f'(ID:{self.id})')
        return response


def construct_trigger(trigger):
    if trigger.type == TASK_TRIGGER_EVENT:
        return IEventTrigger(trigger)
    elif trigger.type == TASK_TRIGGER_BOOT:
        return IBootTrigger(trigger)
    elif trigger.type == TASK_TRIGGER_IDLE:
        return IIdleTrigger(trigger)
    elif trigger.type == TASK_TRIGGER_TIME:
        return ITriggerTime(trigger)
    elif trigger.type == TASK_TRIGGER_LOGON:
        return ILogonTrigger(trigger)
    elif trigger.type == TASK_TRIGGER_DAILY:
        return ITrigerDaily(trigger)
    elif trigger.type == TASK_TRIGGER_WEEKLY:
        return IWeeklyTrigger(trigger)
    elif trigger.type == TASK_TRIGGER_MONTHLY:
        return ITriggerMonthly(trigger)
    elif trigger.type == TASK_TRIGGER_MONTHLYDOW:
        return ITriggerDOW(trigger)
    elif trigger.type == TASK_TRIGGER_REGISTRATION:
        return IRegistrationTrigger(trigger)
    elif trigger.type == TASK_TRIGGER_SESSION_STATE_CHANGE:
        return ISessionStateChangeTrigger(trigger)
    elif trigger.type == TASK_TRIGGER_CUSTOM_TRIGGER_01:
        return ICustomTrigger(trigger)
    else:
        return ITrigger(trigger)
