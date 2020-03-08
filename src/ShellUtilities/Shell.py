import subprocess
import logging
import time
from ShellUtilities.ShellCommandException import ShellCommandException
from ShellUtilities.ShellCommandResults import ShellCommandResults

logger = logging.getLogger(__name__).parent

def execute_shell_command(command, max_retries=1, retry_delay=1):

    logging.debug("Running shell command:")
    logging.debug(command)

    for i in range(0, max_retries):
        process = subprocess.Popen([command], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        (stdout, stderr) = process.communicate()
        exitcode = process.returncode

        # The stderr and stdout are byte objects... lets change them to strings
        stdout = stdout.decode()
        stderr = stderr.decode()

        # Sanitize the variables and remove trailing newline characters
        stdout = stdout.rstrip("\n")
        stderr = stderr.rstrip("\n")

        # Set the exit code and return
        if exitcode is 0:
            return ShellCommandResults(command, stdout, stderr, exitcode)

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