import sys
from unittest import mock

import pytest

from qrcode.console_scripts import commas, main


def bad_read():
    msg = "utf-8"
    raise UnicodeDecodeError(msg, b"0x80", 0, 1, "invalid start byte")


@mock.patch("os.isatty", return_value=True)
@mock.patch("qrcode.main.QRCode.print_ascii")
def test_isatty(mock_print_ascii, mock_isatty):
    main(["testtext"])
    mock_print_ascii.assert_called_with(tty=True)


@mock.patch("os.isatty", return_value=True)
@mock.patch("sys.stdout.isatty", return_value=True)
def test_piped(mock_stdout_isatty, mock_isatty):
    pytest.importorskip("PIL", reason="Requires PIL")
    main(["testtext"])


@mock.patch("os.isatty", return_value=True)
def test_stdin(mock_isatty):
    with (
        mock.patch("qrcode.main.QRCode.print_ascii") as mock_print_ascii,
        mock.patch("sys.stdin") as mock_stdin,
    ):
        mock_stdin.buffer.read.return_value = "testtext"
        main([])
        assert mock_stdin.buffer.read.called
        mock_print_ascii.assert_called_with(tty=True)


@mock.patch("os.isatty", return_value=True)
def test_stdin_py3_unicodedecodeerror(mock_isatty):
    with (
        mock.patch("qrcode.main.QRCode.print_ascii") as mock_print_ascii,
        mock.patch("sys.stdin") as mock_stdin,
    ):
        mock_stdin.buffer.read.return_value = "testtext"
        mock_stdin.read.side_effect = bad_read
        # sys.stdin.read() will raise an error...
        with pytest.raises(UnicodeDecodeError):
            sys.stdin.read()
        # ... but it won't be used now.
        main([])
        mock_print_ascii.assert_called_with(tty=True)


def test_optimize():
    pytest.importorskip("PIL", reason="Requires PIL")
    main(["testtext", "--optimize", "0"])


def test_factory():
    main(["testtext", "--factory", "svg"])


def test_bad_factory():
    with pytest.raises(SystemExit):
        main(["testtext", "--factory", "nope"])


@mock.patch.object(sys, "argv", ["qr", "testtext", "output"])
def test_sys_argv():
    pytest.importorskip("PIL", reason="Requires PIL")
    main()


def test_output(tmp_path):
    pytest.importorskip("PIL", reason="Requires PIL")
    main(["testtext", "--output", str(tmp_path / "test.png")])


def test_factory_drawer_none(capsys):
    pytest.importorskip("PIL", reason="Requires PIL")
    with pytest.raises(SystemExit):
        main(["testtext", "--factory", "pil", "--factory-drawer", "nope"])
    assert "The selected factory has no drawer aliases" in capsys.readouterr()[1]


def test_factory_drawer_bad(capsys):
    with pytest.raises(SystemExit):
        main(["testtext", "--factory", "svg", "--factory-drawer", "sobad"])
    assert "sobad factory drawer not found" in capsys.readouterr()[1]


def test_factory_drawer(capsys):
    main(["testtext", "--factory", "svg", "--factory-drawer", "circle"])


def test_commas():
    assert commas([]) == ""
    assert commas(["A"]) == "A"
    assert commas("AB") == "A or B"
    assert commas("ABC") == "A, B or C"
    assert commas("ABC", joiner="and") == "A, B and C"
