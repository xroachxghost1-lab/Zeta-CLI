from importlib.metadata import version

import zeta_cli


def test_zeta_package_imports():
    assert zeta_cli.__file__ is not None


def test_zeta_package_version():
    assert version("zeta-cli") == "0.1.0"
