import importlib.util
import errno
from pathlib import Path
import unittest
import tempfile
import subprocess
from unittest.mock import patch


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


class NativeLibraryClosureTests(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).resolve().parents[1] / "runtime_probe.py"
        spec = importlib.util.spec_from_file_location("runtime_probe", path)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def exercise(self, contextual_output, contextual_code=0, bundled=True):
        with tempfile.TemporaryDirectory() as directory:
            prefix = Path(directory).resolve()
            root = prefix / "lib/python3.12/site-packages/psycopg_binary.libs"
            root.mkdir(parents=True)
            target = root / "libpq.so" if bundled else prefix / "lib/libtk.so"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b"\x7fELF")
            executable = prefix / "python"
            calls = []

            def ldd(command, **kwargs):
                calls.append((command, kwargs))
                if command[1] == str(executable):
                    return subprocess.CompletedProcess(
                        command, 0, "libc => /lib/libc.so", ""
                    )
                if "env" in kwargs:
                    return subprocess.CompletedProcess(
                        command, contextual_code, contextual_output, ""
                    )
                return subprocess.CompletedProcess(
                    command, 0, "libmissing.so => not found", ""
                )

            with (
                patch.object(self.module.sys, "prefix", str(prefix)),
                patch.object(self.module.sys, "base_prefix", str(prefix)),
                patch.object(self.module.sys, "executable", str(executable)),
                patch.object(self.module.subprocess, "run", side_effect=ldd),
                patch.dict(self.module.os.environ, {"LD_LIBRARY_PATH": "/unrelated"}),
            ):
                report = self.module.native_libraries()
            return report, calls, str(target), str(root)

    def test_contextual_sibling_closure_retains_first_pass_evidence(self):
        report, calls, target, root = self.exercise("libmissing.so => sibling.so")
        self.assertEqual(report["missing_libraries"], [])
        self.assertEqual(
            report["first_pass_missing"],
            [{"path": target, "output": "libmissing.so => not found"}],
        )
        self.assertTrue(report["contextual_checks"][0]["resolved"])
        contextual = [kwargs for _, kwargs in calls if "env" in kwargs]
        self.assertEqual(contextual[0]["env"]["LD_LIBRARY_PATH"], root)

    def test_genuine_missing_or_failed_context_never_passes(self):
        for output, code in (
            ("libmissing.so => not found", 0),
            ("loader failed", 1),
            ("statically linked", 1),
        ):
            with self.subTest(output=output):
                report, _, target, _ = self.exercise(output, code)
                self.assertEqual(report["missing_libraries"], [target])
                self.assertFalse(report["contextual_checks"][0]["resolved"])

    def test_nonbundled_tk_failure_cannot_borrow_wheel_paths(self):
        report, calls, target, _ = self.exercise(
            "libmissing.so => sibling.so", bundled=False
        )
        self.assertEqual(report["missing_libraries"], [target])
        self.assertEqual(report["contextual_checks"], [])
        self.assertFalse(any("env" in kwargs for _, kwargs in calls))

    def test_native_import_failures_are_explicit(self):
        with patch.object(
            self.module.importlib,
            "import_module",
            side_effect=[object(), ImportError(), object(), object()],
        ):
            self.assertEqual(
                self.module.native_imports("worker"),
                {"psycopg": True, "psycopg_binary": False, "Bio": True, "numpy": True},
            )
        with patch.object(self.module.importlib, "import_module") as load:
            self.assertTrue(all(self.module.native_imports("api").values()))
            self.assertEqual(
                [item.args[0] for item in load.call_args_list],
                ["asyncpg", "cryptography.hazmat.bindings._rust"],
            )
