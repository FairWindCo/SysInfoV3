import inspect


class MethodNotImplementedError(RuntimeError):

    def __init__(self):
        clazz = inspect.stack()[1][0].f_locals.get('self', None).__class__.__name__
        method = inspect.stack()[1].function
        super(MethodNotImplementedError, self).__init__('%s.%s not implemented' % (clazz, method))


class Command(object):

    def build(self):
        raise MethodNotImplementedError()


class CommandRunner(object):

    def run(self, cmd: Command):
        raise MethodNotImplementedError()


class Result(object):

    def __init__(self, success: bool, code: int, out: str, err: str):
        self.success = success
        self.code = code
        self.out = out
        self.err = err
