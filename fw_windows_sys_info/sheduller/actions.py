import os.path
from dataclasses import dataclass

TASK_ACTION_EXEC = 0
TASK_ACTION_COM_HANDLER = 5
TASK_ACTION_SEND_EMAIL = 6
TASK_ACTION_SHOW_MESSAGE = 7


@dataclass
class IAction:
    def __init__(self, action) -> None:
        super().__init__()
        self.id = action.Id

    def __str__(self) -> str:
        return f'fAction({self.id})'

    def short(self):
        return f'I({self.id})'

    def __repr__(self) -> str:
        return self.__str__()


class IComHandlerAction(IAction):
    def __init__(self, action) -> None:
        super().__init__(action)
        self.classid = action.ClassId
        self.data = action.Data

    def __str__(self) -> str:
        return f'IComHandlerAction({self.classid}{"," + self.data if self.data else ""})'

    def short(self):
        return f'DCOM({self.classid})'

    def as_dict(self):
        return {
            'path': self.classid,
            'args': self.data,
            'work': "",
            'type': 'com'
        }


class IEmailAction(IAction):
    def __init__(self, action) -> None:
        super().__init__(action)
        self.subject = action.Subject
        self.to = action.To
        self.reply = action.ReplyTo
        self.server = action.Server
        self.from_f = action.From
        self.headers = action.HeaderFields
        self.body = action.Body
        self.cc = action.Cc
        self.bcc = action.Bcc
        self.atach = action.Attachments

    def __str__(self) -> str:
        return f'MailAction(to={self.to}{", subject=" + self.subject if self.subject else ""})'

    def short(self):
        return f'mail(to={self.to})'

    def as_dict(self):
        return {
            'path': self.to,
            'args': self.subject,
            'work': self.body,
            'type': 'mail'
        }


class IExecAction(IAction):
    def __init__(self, action) -> None:
        super().__init__(action)
        self.path = str(action.Path).lower()
        self.args = action.Arguments
        self.work = action.WorkingDirectory

    def __str__(self) -> str:
        return f'Exec({self.path}{" " + self.args if self.args else ""}){" in " + self.work if self.work else ""}'

    def short(self):
        path = self.path
        if path:
            base = os.path.basename(path)
            if base == 'powershell.exe':
                path = 'powershell.exe'
            elif base == 'cmd.exe':
                path = 'cmd.exe'
        return f'{path} {self.args}'

    def as_dict(self):
        return {
            'path': self.path,
            'args': self.args,
            'work': self.work,
            'type': 'exec'
        }


class IMessageAction(IAction):
    def __init__(self, action) -> None:
        super().__init__(action)
        self.message = action.MessageBody
        self.title = action.Title

    def __str__(self) -> str:
        return f'Message({self.title}:{self.message}'

    def short(self):
        return f'mess({self.title}:{self.message})'

    def as_dict(self):
        return {
            'path': self.title,
            'args': self.message,
            'work': "",
            'type': 'message'
        }


def get_action_def(action):
    ty = action.Type
    if ty == TASK_ACTION_EXEC:
        return IExecAction(action)
    elif ty == TASK_ACTION_COM_HANDLER:
        return IComHandlerAction(action)
    elif ty == TASK_ACTION_SEND_EMAIL:
        return IEmailAction(action)
    elif ty == TASK_ACTION_SHOW_MESSAGE:
        return IMessageAction(action)
    else:
        return IAction(action)
