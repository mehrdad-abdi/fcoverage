from unittest.mock import patch

import pytest

from fcoverage.utils.code.pytest_utils import (
    list_available_fixtures,
)

COMMAND_OUT = """cache -- .venv/lib/python3.13/site-packages/_pytest/cacheprovider.py:555
    Return a cache object that can persist state between testing sessions.

capsys -- .venv/lib/python3.13/site-packages/_pytest/capture.py:1000
    Enable text capturing of writes to ``sys.stdout`` and ``sys.stderr``.

capteesys -- .venv/lib/python3.13/site-packages/_pytest/capture.py:1028
    Enable simultaneous text capturing and pass-through of writes
    to ``sys.stdout`` and ``sys.stderr`` as defined by ``--capture=``.

capsysbinary -- .venv/lib/python3.13/site-packages/_pytest/capture.py:1063
    Enable bytes capturing of writes to ``sys.stdout`` and ``sys.stderr``.

capfd -- .venv/lib/python3.13/site-packages/_pytest/capture.py:1091
    Enable text capturing of writes to file descriptors ``1`` and ``2``.

capfdbinary -- .venv/lib/python3.13/site-packages/_pytest/capture.py:1119
    Enable bytes capturing of writes to file descriptors ``1`` and ``2``.

doctest_namespace [session scope] -- .venv/lib/python3.13/site-packages/_pytest/doctest.py:740
    Fixture that returns a :py:class:`dict` that will be injected into the
    namespace of doctests.

pytestconfig [session scope] -- .venv/lib/python3.13/site-packages/_pytest/fixtures.py:1424
    Session-scoped fixture that returns the session's :class:`pytest.Config`
    object.

record_property -- .venv/lib/python3.13/site-packages/_pytest/junitxml.py:277
    Add extra properties to the calling test.

record_xml_attribute -- .venv/lib/python3.13/site-packages/_pytest/junitxml.py:300
    Add extra xml attributes to the tag for the calling test.

record_testsuite_property [session scope] -- .venv/lib/python3.13/site-packages/_pytest/junitxml.py:338
    Record a new ``<property>`` tag as child of the root ``<testsuite>``.

tmpdir_factory [session scope] -- .venv/lib/python3.13/site-packages/_pytest/legacypath.py:298
    Return a :class:`pytest.TempdirFactory` instance for the test session.

tmpdir -- .venv/lib/python3.13/site-packages/_pytest/legacypath.py:305
    Return a temporary directory (as `legacy_path`_ object)
    which is unique to each test function invocation.
    The temporary directory is created as a subdirectory
    of the base temporary directory, with configurable retention,
    as discussed in :ref:`temporary directory location and retention`.

caplog -- .venv/lib/python3.13/site-packages/_pytest/logging.py:596
    Access and control log capturing.

monkeypatch -- .venv/lib/python3.13/site-packages/_pytest/monkeypatch.py:31
    A convenient fixture for monkey-patching.

recwarn -- .venv/lib/python3.13/site-packages/_pytest/recwarn.py:34
    Return a :class:`WarningsRecorder` instance that records all warnings emitted by test functions.

tmp_path_factory [session scope] -- .venv/lib/python3.13/site-packages/_pytest/tmpdir.py:240
    Return a :class:`pytest.TempPathFactory` instance for the test session.

tmp_path -- .venv/lib/python3.13/site-packages/_pytest/tmpdir.py:255
    Return a temporary directory (as :class:`pathlib.Path` object)
    which is unique to each test function invocation.
    The temporary directory is created as a subdirectory
    of the base temporary directory, with configurable retention,
    as discussed in :ref:`temporary directory location and retention`.


------------------ fixtures defined from anyio.pytest_plugin -------------------
anyio_backend [module scope] -- .venv/lib/python3.13/site-packages/anyio/pytest_plugin.py:174
    no docstring available

anyio_backend_name -- .venv/lib/python3.13/site-packages/anyio/pytest_plugin.py:179
    no docstring available

anyio_backend_options -- .venv/lib/python3.13/site-packages/anyio/pytest_plugin.py:187
    no docstring available

free_tcp_port_factory [session scope] -- .venv/lib/python3.13/site-packages/anyio/pytest_plugin.py:256
    no docstring available

free_udp_port_factory [session scope] -- .venv/lib/python3.13/site-packages/anyio/pytest_plugin.py:261
    no docstring available

free_tcp_port -- .venv/lib/python3.13/site-packages/anyio/pytest_plugin.py:266
    no docstring available

free_udp_port -- .venv/lib/python3.13/site-packages/anyio/pytest_plugin.py:271
    no docstring available


------------------- fixtures defined from pytest_cov.plugin --------------------
no_cover -- .venv/lib/python3.13/site-packages/pytest_cov/plugin.py:433
    A pytest fixture to disable coverage.

cov -- .venv/lib/python3.13/site-packages/pytest_cov/plugin.py:438
    A pytest fixture to provide access to the underlying coverage object.


------------------------ fixtures defined from conftest ------------------------
fixture_3 -- tests/conftest.py:14
    no docstring available

fixture_1 -- tests/conftest.py:4
    no docstring available

fixture_2 -- tests/conftest.py:9
    no docstring available


----------------------- fixtures defined from test_greet -----------------------
fixture_3 -- tests/test_greet.py:5
    no docstring available


no tests ran in 0.01s
"""


@pytest.fixture
def mock_command_output():
    with patch("fcoverage.utils.code.pytest_utils.run_cmd") as mock_cmd:
        mock_cmd.return_value = COMMAND_OUT.splitlines()
        yield mock_cmd


def test_list_fixtures(mock_command_output):
    fixtures = list_available_fixtures(
        "project", "tests/test_greet.py", ["tests/"], "src"
    )

    assert len(fixtures) == 3
    assert "fixture_1" in fixtures
    assert "fixture_2" in fixtures
    assert "fixture_3" in fixtures
    assert fixtures["fixture_1"]["path"] == "tests/conftest.py"
    assert fixtures["fixture_2"]["path"] == "tests/conftest.py"
    assert (
        fixtures["fixture_3"]["path"] == "tests/test_greet.py"
    ), "fixture precendence should be respected"
