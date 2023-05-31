import subprocess
import logging
import time
from ShellUtilities.ShellCommandException import ShellCommandException
from ShellUtilities.ShellCommandResults import ShellCommandResults, AsynchronousShellCommandResults
import os
import threading
import queue
import asyncio
import json


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
    if executable:
        logging.debug(f"Executable set to: {executable}")
        kwargs["executable"] = executable
    if env:
        logging.debug(f"Environment set to: " + os.linesep + json.dumps(env, indent = 4))
        kwargs["env"] = env
    if cwd:
        logging.debug(f"CWD set to: {cwd}")
        kwargs["cwd"] = cwd

    # Create the process
    process = subprocess.Popen(*args, **kwargs)

    logging.debug("Process opened.")
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
                return AsynchronousShellCommandResults(command, process)

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
