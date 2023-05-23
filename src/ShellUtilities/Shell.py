import subprocess
import logging
import time
from ShellUtilities.ShellCommandException import ShellCommandException
from ShellUtilities.ShellCommandResults import ShellCommandResults
import os
import threading
import queue
import asyncio

logger = logging.getLogger(__name__).parent

def __execute_shell_command(command, env, cwd, executable=None):
    # Create the process and wait for the exit
    process = __execute_shell_command_async(command, env, cwd, executable)
    (stdout, stderr) = process.communicate()
    exitcode = process.returncode

    # The stderr and stdout are byte objects... lets change them to strings
    stdout = stdout.decode()
    stderr = stderr.decode()

    # Sanitize the variables and remove trailing newline characters
    stdout = stdout.rstrip("\n")
    stderr = stderr.rstrip("\n")

    return exitcode, stdout, stderr


def __execute_shell_command_async(command, env, cwd, executable=None):

    args = [command]
    kwargs = {
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "shell": True,
        "close_fds": 'posix',
    }
    logging.debug(f"Executable set to: {executable}")

    if executable:
        kwargs["executable"] = executable
    if env:
        kwargs["env"] = env
    if cwd:
        kwargs["cwd"] = cwd

    # Create the process
    process = subprocess.Popen(*args, **kwargs)

    return process


def execute_shell_command(command, max_retries=1, retry_delay=1, env=None, cwd=None, blocking=True, executable=None):

    try:

        if cwd and not os.path.isdir(cwd):
            raise Exception("The working directory '{0}' does not exist.".format(cwd))

        logging.debug("Running shell command:")
        logging.debug(command)

        for i in range(0, max_retries):

            # Run the shell command
            if blocking:
                exitcode, stdout_string, stderr_string = __execute_shell_command(command, env, cwd, executable)
            else:
                process = __execute_shell_command_async(command, env, cwd, executable)
                return process

            # Set the exit code and return
            if exitcode == 0:
                return ShellCommandResults(command, stdout_string, stderr_string, exitcode)

            # If an error occured we need to determine if this is the last retry attempt
            last_retry = i == max_retries - 1

            # If it is not the last retry we must determine whether or not we can ignore the error
            # To do this we must see if our retry conditions have been satisfied
            if not last_retry:
                logging.debug("Retrying...(%s)" % i)
                time.sleep(retry_delay)
                continue
            else:
                err_msg = "Maximum retries (%s) exceeded for shell command."
                err_msg += " An error will be generated."
                logging.error(err_msg % max_retries)
                logging.error("Stdout:")
                for line in stdout_string.split("\n"):
                    logging.error(line)
                logging.error("Stderr:")
                for line in stderr_string.split("\n"):
                    logging.error(line)
                logging.error("Exit code: {0}".format(exitcode))

                raise ShellCommandException(command, stdout_string, stderr_string, exitcode)

    except Exception as ex:
        raise Exception("An error occurred while executing the shell command.") from ex


def handle_asynchronous_output(process, stdout_func, stderr_func):

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

    stdout_lock = threading.Lock()
    stderr_lock = threading.Lock()

    stdout_queue = queue.Queue()
    stderr_queue = queue.Queue()

    def enqueue_buffer(buffer, buffer_queue, buffer_lock):
        enqueue = True
        while enqueue:
            for line in iter(buffer.readline, b''):
                if line != b'':
                    buffer_lock.acquire()
                    buffer_queue.put(line)
                    buffer_lock.release()
            enqueue = process.poll() != 0

    stdout_enqueue_thread = threading.Thread(target=enqueue_buffer, args=(process.stdout, stdout_queue, stdout_lock))
    stderr_enqueue_thread = threading.Thread(target=enqueue_buffer, args=(process.stderr, stderr_queue, stderr_lock))
    stdout_enqueue_thread.start()
    stderr_enqueue_thread.start()

    def read_from_queue(buffer_queue, line_func, buffer_lock):
        read = True
        while read:
            empty = False
            while not empty:
                try:
                    buffer_lock.acquire()
                    line = buffer_queue.get_nowait()
                    buffer_lock.release()
                    line = line.decode()
                    line = line.rstrip("\n")
                    line_func(line)
                except queue.Empty:
                    if buffer_lock.locked():
                        buffer_lock.release()
                    time.sleep(0.01)


                buffer_lock.acquire()
                empty = buffer_queue.empty()
                buffer_lock.release()

            read = process.poll() != 0

    stdout_read_thread = threading.Thread(target=read_from_queue, args=[stdout_queue, stdout_func, stdout_lock])
    stderr_read_thread = threading.Thread(target=read_from_queue, args=[stderr_queue, stderr_func, stderr_lock])
    stdout_read_thread.start()
    stderr_read_thread.start()

    threads = (stdout_enqueue_thread, stderr_enqueue_thread, stdout_read_thread, stderr_read_thread)
    return threads


def wait(shell_process, output_handling_threads):

    # This is a blocking function which will safely wait for the shell process and handling threads to complete

    # Wait for the process to exit
    shell_process.wait()

    # Wait for the enqueing threads to complete
    while output_handling_threads[0].is_alive() or output_handling_threads[1].is_alive():
        time.sleep(0.01)

    # Wait for the queue reading functions to complete
    while output_handling_threads[2].is_alive() or output_handling_threads[3].is_alive():
        time.sleep(0.01)

    # Make sure we have cleaned up and dont see any warnings like:
    # ResourceWarning: unclosed file <_io.BufferedReader name=4>
    shell_process.stdout.close()
    shell_process.stderr.close()
