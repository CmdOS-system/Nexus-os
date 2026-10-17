import unittest
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from installer_executor import install

class TestInstallerExecutor(unittest.TestCase):
    @patch("installer_executor.run_cmd")
    @patch("time.sleep")
    @patch("pathlib.Path.mkdir")
    @patch("builtins.open")
    @patch("subprocess.run")
    def test_install_vdb(self, mock_subprocess_run, mock_open, mock_mkdir, mock_sleep, mock_run_cmd):
        mock_subprocess_run.return_value = MagicMock(stdout="fake-uuid\n")

        install("/dev/vdb")

        # Verify formatting happened on the right partitions
        mock_run_cmd.assert_any_call(["mkfs.fat", "-F32", "/dev/vdb1"])
        mock_run_cmd.assert_any_call(["mkfs.ext4", "-F", "/dev/vdb2"])

    @patch("installer_executor.run_cmd")
    @patch("time.sleep")
    @patch("pathlib.Path.mkdir")
    @patch("builtins.open")
    @patch("subprocess.run")
    def test_install_nvme(self, mock_subprocess_run, mock_open, mock_mkdir, mock_sleep, mock_run_cmd):
        mock_subprocess_run.return_value = MagicMock(stdout="fake-uuid\n")

        install("/dev/nvme0n1")

        # Verify formatting happened on the right partitions
        mock_run_cmd.assert_any_call(["mkfs.fat", "-F32", "/dev/nvme0n1p1"])
        mock_run_cmd.assert_any_call(["mkfs.ext4", "-F", "/dev/nvme0n1p2"])

    @patch("installer_executor.run_cmd")
    @patch("time.sleep")
    @patch("pathlib.Path.mkdir")
    @patch("builtins.open")
    @patch("subprocess.run")
    def test_install_mmcblk(self, mock_subprocess_run, mock_open, mock_mkdir, mock_sleep, mock_run_cmd):
        mock_subprocess_run.return_value = MagicMock(stdout="fake-uuid\n")

        install("/dev/mmcblk0")

        # Verify formatting happened on the right partitions
        mock_run_cmd.assert_any_call(["mkfs.fat", "-F32", "/dev/mmcblk0p1"])
        mock_run_cmd.assert_any_call(["mkfs.ext4", "-F", "/dev/mmcblk0p2"])

if __name__ == "__main__":
    unittest.main()
