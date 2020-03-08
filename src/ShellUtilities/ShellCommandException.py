class ShellCommandException(Exception):

    def __init__(self, command, stdout, stderr, exitcode):
        self.Command = command
        self.Stdout = stdout
        self.Stderr = stderr
        self.ExitCode = exitcode

        msg = stderr
        if not stderr:
            msg = stdout
        super(ShellCommandException, self).__init__(msg)