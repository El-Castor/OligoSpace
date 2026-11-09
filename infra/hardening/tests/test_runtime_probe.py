import importlib.util
import errno
from pathlib import Path
import unittest


class RuntimeProbeTests(unittest.TestCase):
    def test_readonly_root_requires_mount_flag_and_rejected_write(self):
        path = Path(__file__).resolve().parents[1] / "runtime_probe.py"
        spec = importlib.util.spec_from_file_location("runtime_probe", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        readonly = "overlay / overlay ro,relatime 0 0\ntmpfs /tmp tmpfs rw 0 0\n"
        writable = "overlay / overlay rw,relatime 0 0\n"
        self.assertTrue(module.readonly_root_proven(readonly, errno.EROFS))
        self.assertTrue(module.readonly_root_proven(readonly, errno.EACCES))
        self.assertFalse(module.readonly_root_proven(writable, errno.EACCES))
        self.assertFalse(module.readonly_root_proven(writable, errno.EROFS))
        self.assertFalse(module.readonly_root_proven(readonly, None))
        self.assertFalse(module.readonly_root_proven("", errno.EACCES))

    def test_proc_status_requires_explicit_zero_capabilities_and_nnp(self):
        path = Path(__file__).resolve().parents[1] / "runtime_probe.py"
        spec = importlib.util.spec_from_file_location("runtime_probe", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertTrue(module.hardened_status("CapEff:\t00000000\nNoNewPrivs:\t1\n"))
        for status in ("", "CapEff:\t1\nNoNewPrivs:\t1", "CapEff:\t0\nNoNewPrivs:\t0"):
            self.assertFalse(module.hardened_status(status))
