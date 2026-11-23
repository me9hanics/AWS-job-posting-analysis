import unittest
from pathlib import Path

from jobscraping.config.configs import REPO_ROOT_PATH


class TestConfigPaths(unittest.TestCase):
    def test_repo_root_is_the_repository(self):
        self.assertTrue((Path(REPO_ROOT_PATH) / "pyproject.toml").exists())


if __name__ == "__main__":
    unittest.main()
