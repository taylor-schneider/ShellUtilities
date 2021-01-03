from unittest import TestCase
from ShellUtilities import Shell
import platform
import os


class Tes_Shell(TestCase):

    def test__execute_shell_command__success__simple_pwd(self):
        system_name = platform.system()
        if system_name == 'Windows':
            shell_command_string = r'cd'
        else:
            shell_command_string = "pwd"
        shell_command_result = Shell.execute_shell_command(shell_command_string)
        self.assertEqual(0, shell_command_result.ExitCode)
        self.assertEqual("", shell_command_result.Stderr)
        self.assertNotEqual("", shell_command_result.Stdout)
        current_dir = os.path.dirname(os.path.abspath(__file__))
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




