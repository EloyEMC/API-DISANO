from pathlib import Path


ROOT = Path(__file__).parents[2]


def test_scripts_do_not_print_secret_values_or_use_shell_execution():
    setup = (ROOT / "scripts/setup.sh").read_text()
    pytest_runner = (ROOT / "scripts/run_pytest.py").read_text()
    env_runner = (ROOT / "scripts/run_pytest_with_env.sh").read_text()

    assert "API Key generada: $API_KEY" not in setup
    assert "os.environ['API_KEYS']" not in pytest_runner
    assert "os.environ['ADMIN_API_KEYS']" not in pytest_runner
    assert "shell=True" not in env_runner
