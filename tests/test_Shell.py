from unittest import TestCase
from ShellUtilities import Shell
from ShellUtilities.ShellCommandResults import ShellCommandResults
import platform
import os
import time
import threading
import queue
import tracemalloc
import logging


logging.basicConfig(level=logging.DEBUG)


tracemalloc.start()


class Test_Shell(TestCase):

    def test__execute_shell_command__success__simple_pwd(self):
        system_name = platform.system()
        if system_name == 'Windows':
            shell_command_string = r'cd'
        else:
            shell_command_string = "pwd"
        current_dir = os.path.dirname(os.path.abspath(__file__))
        shell_command_result = Shell.execute_shell_command(shell_command_string, env={}, cwd=current_dir)
        self.assertEqual(0, shell_command_result.ExitCode)
        self.assertEqual("", shell_command_result.Stderr)
        self.assertNotEqual("", shell_command_result.Stdout)
        self.assertEqual(current_dir, shell_command_result.Stdout.strip())

    def test__execute_shell_command__success__pwd_from_cwd(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)

        system_name = platform.system()
        if system_name == 'Windows':
            shell_command_string = r'cd'
        else:
            shell_command_string = "pwd"
        shell_command_result = Shell.execute_shell_command(shell_command_string, cwd=parent_dir)
        self.assertEqual(0, shell_command_result.ExitCode)
        self.assertEqual("", shell_command_result.Stderr)
        self.assertNotEqual("", shell_command_result.Stdout)
        self.assertEqual(parent_dir, shell_command_result.Stdout.strip())

    def test__execute_shell_command__success__non_blocking(self):
        shell_command_string = r"echo 'a'; sleep 2; echo 'b'"
        shell_command_results = Shell.execute_shell_command(shell_command_string, blocking=False)
        shell_command_results.wait()

        self.assertEqual(0, shell_command_results.exit_code)
        self.assertTrue(shell_command_results.pid > 0)
        self.assertIsNotNone(shell_command_results.Stdout)
        self.assertEqual("a" + os.linesep + "b" + os.linesep, shell_command_results.Stdout)
        self.assertEqual("", shell_command_results.Stderr)
        self.assertEqual(2, len(shell_command_results.stdout_lines))
        self.assertEqual(0, len(shell_command_results.stderr_lines))

    def test__execute_shell_command__success__default_shell(self):
        shell_command_string = 'echo "$SHELL"'
        shell_command_result = Shell.execute_shell_command(shell_command_string)
        self.assertEqual(0, shell_command_result.ExitCode)
        self.assertEqual("", shell_command_result.Stderr)
        self.assertEqual("/bin/bash", shell_command_result.Stdout)

    def test__execute_shell_command__success__bash_shell(self):
        shell_command_string = 'echo "$SHELL"'
        shell_command_result = Shell.execute_shell_command(shell_command_string, executable="/bin/bash")
        self.assertEqual(0, shell_command_result.ExitCode)
        self.assertEqual("", shell_command_result.Stderr)
        self.assertEqual("/bin/bash", shell_command_result.Stdout)

    def test__execute_shell_command__success__sh_shell(self):
        # The shell variable is set by the parent shell, which is bash in most environments
        # So it will be misleading
        shell_command_string = 'echo "$SHELL"'
        shell_command_result = Shell.execute_shell_command(shell_command_string, executable="/bin/sh")
        self.assertEqual(0, shell_command_result.ExitCode)
        self.assertEqual("", shell_command_result.Stderr)
        self.assertEqual("/bin/bash", shell_command_result.Stdout)
        
        # Something gets screwed up and we do not see exactly the same thing as the command line
        shell_command_string = r"cat /proc/$$/cmdline"
        shell_command_result = Shell.execute_shell_command(r'echo "/proc/$$/cmdline" | xargs -I {} cat {}')
        self.assertEqual(0, shell_command_result.ExitCode)
        self.assertEqual("", shell_command_result.Stderr)
        self.assertIn("/bin/sh", shell_command_result.Stdout)

    def test__handle_asynchronous_output__success__shell_command(self):
        shell_command_string = r"echo 'a'; sleep 2; echo 'b'; sleep 2; echo 'c'; sleep 2; echo 'd';"
        process = Shell.execute_shell_command(shell_command_string, blocking=False)
        stdout = []
        stderr = []
        def stdout_func(stdout_line):
            print(stdout_line)
            stdout.append(stdout_line)
        def stderr_func(stderr_line):
            print(stderr_line)
            stderr.append(stderr_line)

        threads = Shell.handle_asynchronous_output(process, stdout_func, stderr_func)
        Shell.wait(process, threads)

        exit_code = process.returncode
        pid = process.pid

        self.assertEqual(0, process.poll())
        self.assertFalse(threads[0].is_alive())
        self.assertFalse(threads[1].is_alive())
        self.assertFalse(threads[2].is_alive())
        self.assertFalse(threads[3].is_alive())
        self.assertEqual(0, exit_code)
        self.assertTrue(pid > 0)
        self.assertEqual(4, len(stdout))
        self.assertEqual(0, len(stderr))

    def test__handle_asynchronous_output__success__script_using_module_code(self):
        # Run a script that takes 25 seconds to run and prints info to the stdout and stderr
        current_directory = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(current_directory, "scripts", "loop.sh")
        shell_command_string = "bash '{0}'".format(script_path)
        process = Shell.execute_shell_command(shell_command_string, blocking=False)
        stdout = []
        stderr = []
        def stdout_func(line):
            print(line)
            stdout.append(line)
        def stderr_func(line):
            print(line)
            stderr.append(line)
        threads = Shell.handle_asynchronous_output(process, stdout_func, stderr_func)
        Shell.wait(process, threads)

        exit_code = process.returncode
        pid = process.pid

        self.assertEqual(0, process.poll())
        self.assertFalse(threads[0].is_alive())
        self.assertFalse(threads[1].is_alive())
        self.assertFalse(threads[2].is_alive())
        self.assertFalse(threads[3].is_alive())
        self.assertEqual(0, process.poll())
        self.assertEqual(0, exit_code)
        self.assertTrue(pid > 0)
        self.assertEqual(25, len(stdout))
        self.assertEqual(2, len(stderr))
