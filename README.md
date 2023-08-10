# Overview
This library provides a utility to make executing shell commands much simpler than would be posisble using standard modules. It is built on top of the `subprocess` module and uses it's `subprocess.Popen()` function to execute a shell commands. The library allows shell commands to be executed synchronously (blocking) or asynchronously (non-blocking). It also has utility functions to collect information about the execution such as the ExitCode, the Stdout, and the Stderr.

# How It Works

The `Shell` module provides the `execute_shell_command()` function as the main entry point. This fucntion accepts a number of parameters and allows the user to:
- specify environment variables
- specify the working directory
- specify the shell being used
- specify the number of retries to attempt in the event of a failure
- specify the delay between reties
- specify whether the execution should be blocking or non blocking

In the event of a success (zero exit code) the function will return a [ShellCommandResults object](src/ShellUtilities/ShellCommandResults.py). This object contains pointers to the command, the exit code, the Stdout, and the stderr.

**Note**: The Stdout and Stderr are strings which are decoded from the original byte stream. They will contain all the newlines that were written out to the shell.

In the event of a failure, the function will raise a [ShellCommandException](src/ShellUtilities/ShellCommandException.py) which extends the Exception base class. Like the ShellCommandResults object, this exception contains pointers to the command, the exit code, the Stdout, and the stderr.

# Getting Started

Here is an example of the simple use case for this utility:

```
from ShellUtilities import Shell

shell_command_results = Shell.execute_shell_command("echo $MYVAR", env={"MYVAR": "Hello, World!"})
shell_command_results.ExitCode == 0
print(shell_command_results.StdOut) # Hello, World!
print(shell_command_results.Stderr)
```

And here is a more complex example of this utility running a long command asynchronously while piping the output to stdout in real time:

```
from ShellUtilities import Shell

# Define an async function to use when we execute the shell command
def stdout_func(stdout_line):
    print(stdout_line)
    
# Run the command and also output while the command is running
shell_command_string = r"echo 'a'; sleep 2; echo 'b'; sleep 2; echo 'c'; sleep 2; echo 'd';"
shell_command_results = Shell.execute_shell_command(shell_command_string, blocking=False, async_buffer_funcs={"stdout": [stdout_func]})
time.sleep(1)
print("hello")
shell_command_results.wait()

# The output of this main thread will be:
# a
# hello
# b
# c
# d
```