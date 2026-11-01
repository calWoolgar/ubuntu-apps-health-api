"""The public-repository deployer trusts only successful main push CI runs."""

import importlib.util
from pathlib import Path
import unittest


def load_module():
    script = Path(__file__).resolve().parents[1] / "scripts" / "PollDeploy.py"
    spec = importlib.util.spec_from_file_location("poll_deploy", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SHA = "a" * 40


class PollDeployTests(unittest.TestCase):
    def test_only_successful_main_push_for_exact_sha_is_trusted(self):
        module = load_module()
        run = {
            "head_sha": SHA,
            "head_branch": "main",
            "event": "push",
            "path": ".github/workflows/ci.yaml",
            "status": "completed",
            "conclusion": "success",
            "head_repository": {"full_name": "calWoolgar/ubuntu-apps-health-api"},
        }
        self.assertTrue(module.is_successful_main_run(run, SHA))
        for field, value in [
            ("head_sha", "b" * 40),
            ("head_branch", "feature"),
            ("event", "pull_request"),
            ("path", ".github/workflows/other.yaml"),
            ("status", "in_progress"),
            ("conclusion", "failure"),
            ("conclusion", "cancelled"),
            ("head_repository", {"full_name": "attacker/fork"}),
        ]:
            with self.subTest(field=field, value=value):
                self.assertFalse(module.is_successful_main_run({**run, field: value}, SHA))
        self.assertFalse(module.is_successful_main_run({}, SHA))


if __name__ == "__main__":
    unittest.main()
