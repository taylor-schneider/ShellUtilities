class ShellCommandResults():

    def __init__(self, command, stdout, stderr, exitcode):
        self.Command = command
        self.Stdout = stdout
        self.Stderr = stderr
        self.ExitCode = exitcode
