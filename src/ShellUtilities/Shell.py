import subprocess
import logging
import time
from ShellUtilities.ShellCommandException import ShellCommandException
from ShellUtilities.ShellCommandResults import ShellCommandResults
import os
import operator
import threading

logger = logging.getLogger(__name__).parent

def __execute_shell_command(command, env, cwd):

    args = [command]
    kwargs = {
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "shell": True
    }
    if env:
        kwargs["env"] = env
    if cwd:
        kwargs["cwd"] = cwd

    # Create the process
    process = subprocess.Popen(*args, **kwargs)

    (stdout, stderr) = process.communicate()
    exitcode = process.returncode

    # The stderr and stdout are byte objects... lets change them to strings
    stdout = stdout.decode()
    stderr = stderr.decode()

    # Sanitize the variables and remove trailing newline characters
    stdout = stdout.rstrip("\n")
    stderr = stderr.rstrip("\n")

    return exitcode, stdout, stderr


def __execute_shell_command_async(command, env, cwd):
    args = [command]
    kwargs = {
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "shell": True
    }
    if env:
        kwargs["env"] = env
    if cwd:
        kwargs["cwd"] = cwd

    # Create the process
    process = subprocess.Popen(*args, **kwargs)

    return process


def execute_shell_command(command, max_retries=1, retry_delay=1, env=None, cwd=None, blocking=True):

    try:

        if cwd and not os.path.isdir(cwd):
            raise Exception("The working directory '{0}' does not exist.".format(cwd))

        logging.debug("Running shell command:")
        logging.debug(command)

        for i in range(0, max_retries):

            # Run the shell command
            if blocking:
                exitcode, stdout_string, stderr_string = __execute_shell_command(command, env, cwd)
            else:
                process = __execute_shell_command_async(command, env, cwd)
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
                for line in stdout.split("\n"):
                    print(line)
                logging.error("Stderr:")
                for line in stderr.split("\n"):
                    print(line)
                logging.error("Exit code: {0}".format(exitcode))

                raise ShellCommandException(command, stdout, stderr, exitcode)

    except Exception as ex:
        raise Exception("An error occurred while executing the shell command.") from ex


def __capture_output(process, stdout_func, stderr_func):

    # This is a blocking function that will invoke functions for each line of stdout/etderr that is received in real time

    while True:
        stdout_line = process.stdout.readline().decode().strip("\n")
        stderr_line = process.stderr.readline().decode().strip("\n")
        output_found = False
        if stdout_line:
            stdout_func(stdout_line)
        if stderr_line:
            stderr_func(stderr_line)

        poll = process.poll()
        process_alive = poll is None

        if not output_found and not process_alive:
            break

        if not output_found:
            time.sleep(0.5)


def handle_asynchronous_output(process, stdout_func, stderr_func):

    thread = threading.Thread(target=__capture_output, args=[process, stdout_func, stderr_func])
    thread.start()
    return thread


def wait(shell_process, output_handling_thread):
    shell_process.wait()
    while output_handling_thread.isAlive():
        time.sleep(0.5)
