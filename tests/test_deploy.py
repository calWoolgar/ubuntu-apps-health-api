"""Exercise deployment orchestration without touching a real Docker engine."""

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "Deploy.sh"


class DeploymentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        self.source.mkdir()
        self.run_git("init", "-q")
        self.run_git("config", "user.name", "Deployment tests")
        self.run_git("config", "user.email", "tests@example.invalid")
        (self.source / "compose.yaml").write_text("services: {}\n")
        (self.source / "tracked.txt").write_text("committed source\n")
        self.run_git("add", ".")
        self.run_git("commit", "-qm", "fixture")
        self.revision = self.run_git("rev-parse", "HEAD").strip()
        (self.source / "untracked-secret.txt").write_text("do not deploy\n")

        self.deploy_root = self.root / "deployment"
        self.previous = self.deploy_root / "releases" / "26bf6b0"
        self.previous.mkdir(parents=True)
        (self.previous / "compose.yaml").write_text("services: {}\n")
        (self.deploy_root / "current").symlink_to(self.previous)
        self.config = self.deploy_root / ".env"
        self.config.write_text("API_BIND_ADDRESS=127.0.0.1\nAPI_PORT=8080\nIMAGE_TAG=26bf6b0\n")
        self.config_before = self.config.read_bytes()
        self.calls_path = self.root / "docker-calls.jsonl"
        bin_dir = self.root / "bin"
        bin_dir.mkdir()
        docker = bin_dir / "docker"
        docker.write_text('''#!/usr/bin/env python3
import json, os, sys
args = sys.argv[1:]
tag = os.environ.get("IMAGE_TAG")
with open(os.environ["DOCKER_CALLS"], "a") as stream:
    stream.write(json.dumps({"args": args, "tag": tag}) + "\\n")
if "build" in args and os.environ.get("FAIL_BUILD") == "1":
    sys.exit(1)
if "up" in args and tag == os.environ["NEW_REVISION"] and os.environ.get("FAIL_UP") == "1":
    sys.exit(1)
''')
        docker.chmod(0o755)
        curl = bin_dir / "curl"
        curl.write_text('''#!/usr/bin/env python3
import json, os, sys
if sys.argv[-1].endswith("/version"):
    print(json.dumps({"commitSha": os.environ.get("VERSION_SHA", os.environ["NEW_REVISION"])}))
    sys.exit(0)
if os.environ.get("FAIL_HEALTH") == "1":
    sys.exit(22)
print(os.environ.get("HEALTH_BODY", "Healthy"), end="")
''')
        curl.chmod(0o755)
        self.env = {
            **os.environ,
            "PATH": str(bin_dir) + os.pathsep + os.environ["PATH"],
            "DEPLOY_ROOT": str(self.deploy_root),
            "DEPLOY_HEALTH_URL": "http://127.0.0.1:8080/health",
            "DOCKER_CALLS": str(self.calls_path),
            "NEW_REVISION": self.revision,
        }

    def run_git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.source, text=True)

    def deploy(self, revision=None, **extra_env):
        return subprocess.run(
            ["bash", str(SCRIPT), revision or self.revision],
            cwd=self.source, env={**self.env, **extra_env},
            text=True, capture_output=True,
        )

    def calls(self):
        if not self.calls_path.exists():
            return []
        return [json.loads(line) for line in self.calls_path.read_text().splitlines()]

    def test_success_deploys_exact_revision_and_preserves_configuration(self):
        result = self.deploy()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        release = (self.deploy_root / "current").resolve()
        self.assertNotEqual(release, self.previous)
        self.assertEqual((release / ".deploy-revision").read_text().strip(), self.revision)
        self.assertEqual((release / "tracked.txt").read_text(), "committed source\n")
        self.assertFalse((release / "untracked-secret.txt").exists())
        self.assertEqual(self.config.read_bytes(), self.config_before)
        activation = [call for call in self.calls() if "up" in call["args"]]
        self.assertEqual([call["tag"] for call in activation], [self.revision])
        self.assertIn("--wait", activation[0]["args"])

    def test_build_failure_does_not_replace_running_release(self):
        result = self.deploy(FAIL_BUILD="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.deploy_root / "current").resolve(), self.previous)
        self.assertTrue(any("build" in call["args"] for call in self.calls()))
        self.assertFalse(any("up" in call["args"] for call in self.calls()))

    def test_activation_failure_restores_previous_image(self):
        result = self.deploy(FAIL_UP="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.deploy_root / "current").resolve(), self.previous)
        activation = [call for call in self.calls() if "up" in call["args"]]
        self.assertEqual([call["tag"] for call in activation], [self.revision, "26bf6b0"])

    def test_http_health_failure_restores_previous_image(self):
        result = self.deploy(FAIL_HEALTH="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.deploy_root / "current").resolve(), self.previous)
        activation = [call for call in self.calls() if "up" in call["args"]]
        self.assertEqual([call["tag"] for call in activation], [self.revision, "26bf6b0"])

    def test_missing_shared_configuration_fails_before_docker(self):
        self.config.unlink()
        result = self.deploy()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("configuration", result.stderr.lower())
        self.assertEqual(self.calls(), [])

    def test_http_success_with_wrong_health_body_restores_previous_image(self):
        result = self.deploy(HEALTH_BODY="Unhealthy")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.deploy_root / "current").resolve(), self.previous)
        activation = [call for call in self.calls() if "up" in call["args"]]
        self.assertEqual([call["tag"] for call in activation], [self.revision, "26bf6b0"])

    def test_invalid_revision_cannot_be_used_as_a_path(self):
        result = self.deploy(revision="../../escape")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("revision", result.stderr.lower())
        self.assertEqual(self.calls(), [])

    def test_wrong_deployed_commit_rolls_back(self):
        result = self.deploy(VERSION_SHA="b" * 40)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.deploy_root / "current").resolve(), self.previous)
        activation = [call for call in self.calls() if "up" in call["args"]]
        self.assertEqual([call["tag"] for call in activation], [self.revision, "26bf6b0"])


if __name__ == "__main__":
    unittest.main()
