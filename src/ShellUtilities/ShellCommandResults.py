import threading
import os
import time
from ShellUtilities.ShellCommandException import AsynchronousShellCommandException

class ShellCommandResults():

    def __init__(self, command, stdout, stderr, exitcode):
        self.Command = command
        self.Stdout = stdout
        self.Stderr = stderr
        self.ExitCode = exitcode

class AsynchronousShellCommandResults(ShellCommandResults):

    def __init__(self, command, process):
        # Create vars for handling process output
        self.process = process
        self.stdout_lines = []
        self.stderr_lines = []
        self.stdout_lock = threading.Lock()
        self.stderr_lock = threading.Lock()
        self.pid = process.pid
        self.stdout_thread = None
        self.stderr_thread = None
        
        # Call the parent constructor
        stdout = ""
        stderr = ""
        exitcode = -1
        super().__init__(command, stderr, stdout, exitcode)
        
        # Start handling the asynchronous output
        self.handle_asynchronous_output(self.process)
    
    def _handle_stdout_line(self, line):
        try:
            self.stdout_lock.acquire()
            self.stdout_lines.append(line)
            self.Stdout += line + os.linesep
        finally:
            self.stdout_lock.release()
            
    def _handle_stderr_line(self, line):
        try:
            self.stderr_lock.acquire()
            self.stderr_lines.append(line)
            self.Stderr += line + os.linesep
        finally:
            self.stderr_lock.release()
        
    def handle_asynchronous_output(self, process):

        # This function will allow the user to specify a function to be invoked when data
        # is written to the stderr or stdout buffers. There is a caveat to the underlying
        # libraries which casues a deadlock. The tl;dr; is that this method exists to hide
        # the complications.
        #
        # Per the documentation:
        #   stdin, stdout and stderr specify the executed program’s standard input, standard
        #   output and standard error file handles, respectively. Valid values are PIPE,
        #   DEVNULL, an existing file descriptor (a positive integer), an existing
        #   file object, and None. PIPE indicates that a new pipe to the child should be created.
        #   DEVNULL indicates that the special file os.devnull will be used. With the default
        #   settings of None, no redirection will occur; the child’s file handles will be
        #   inherited from the parent. Additionally, stderr can be STDOUT, which indicates that
        #   the stderr data from the applications should be captured into the same file handle as
        #   for stdout.
        #
        #   Note: The Popen.wait() function...
        #
        #   This will deadlock when using stdout=PIPE or stderr=PIPE and the child process
        #   generates enough output to a pipe such that it blocks waiting for the OS pipe buffer
        #   to accept more data. Use Popen.communicate() when using pipes to avoid that.
        #
        #   https://docs.python.org/3/library/subprocess.html
        #
        #
        # Note:
        #   I had a strange issue when setting both stdout and stderr to subprocess.PIPE
        #   There seemed to be a deadlock until the underlying process completed;
        #   Ie. no output was being captured and no callback functions were being invoked
        #
        #   https://stackoverflow.com/questions/12419198/python-subprocess-readlines-hangs
        #
        # It turns out that the process.stdout.readline() function is a blocking one and is
        # causing a deadlock for some readon.
        #
        #   https://stackoverflow.com/questions/375427/a-non-blocking-read-on-a-subprocess-pipe-in-python
        #

        def handle_output_line(buffer, buffer_handler_func):
            process_running = True
            while process_running:
                for line in iter(buffer.readline, b''):
                    if line != b'':
                        line = line.decode()
                        line = line.rstrip("\n")
                        buffer_handler_func(line)
                process_running = process.poll() == None

        self.stdout_thread = threading.Thread(target=handle_output_line, args=(process.stdout, self._handle_stdout_line))
        self.stderr_thread = threading.Thread(target=handle_output_line, args=(process.stderr, self._handle_stderr_line))
        self.stdout_thread.start()
        self.stderr_thread.start()

    def command_running(self):
        poll = self.process.poll()
        if poll == None:
            return True
        return self.stdout_thread.is_alive() or self.stderr_thread.is_alive()

    def wait(self, raise_on_error=True):

        # This is a blocking function which will safely wait for the shell process and handling threads to complete

        # Wait for the process to exit
        self.process.wait()

        # Wait for the enqueing threads to complete
        while self.stdout_thread.is_alive() or self.stderr_thread.is_alive():
            time.sleep(0.01)

        # Make sure we have cleaned up and dont see any warnings like:
        # ResourceWarning: unclosed file <_io.BufferedReader name=4>
        self.process.stdout.close()
        self.process.stderr.close()

        self.ExitCode = self.process.returncode
        
        if raise_on_error and self.ExitCode != 0:
            raise AsynchronousShellCommandException(self)
