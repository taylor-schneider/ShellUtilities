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
        
class AsynchronousShellCommandException(ShellCommandException):
    
    def __init__(self, async_command_results):
        
        self.process = async_command_results.process
        self.stdout_lines = async_command_results.stdout_lines
        self.stderr_lines = async_command_results.stderr_lines
        self.stdout_lock = async_command_results.stdout_lock
        self.stderr_lock = async_command_results.stderr_lock
        self.pid = async_command_results.pid
        self.stdout_thread = async_command_results.stdout_thread
        self.stderr_thread = async_command_results.stderr_thread
        
        super().__init__(
            async_command_results.Command,
            async_command_results.Stdout,
            async_command_results.Stderr,
            async_command_results.ExitCode
        )