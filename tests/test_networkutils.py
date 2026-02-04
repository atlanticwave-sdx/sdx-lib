from unittest.mock import patch, MagicMock
from sdxlib.networkutils import ping_host, check_connection
import subprocess
import socket

@patch("subprocess.run")
def test_ping_host_success(mock_run):
    mock_run.return_value.stdout = "PING success..."
    with patch("sys.stdout", new_callable=MagicMock) as mock_stdout:
        ping_host("example.com")
    mock_stdout.write.assert_called()

@patch("subprocess.run")
def test_ping_host_fail(mock_run):
    mock_run.side_effect = subprocess.CalledProcessError(
        returncode=2,
        cmd=["ping", "-c", "4", "invalid.host"],
        output=b"",
        stderr=b"ping: invalid.host: Temporary failure in name resolution\n"
    )

    with patch("sys.stdout", new_callable=MagicMock) as mock_stdout:
        ping_host("invalid.host")

    calls = [call[0][0].lower() for call in mock_stdout.write.call_args_list]
    output = " ".join(calls)

    assert "error" in output or "failed" in output or "failure" in output or "resolution" in output
    assert mock_run.called

@patch("subprocess.run")
def test_ping_host_success(mock_run):
    mock_run.return_value = MagicMock(stdout="PING success 64 bytes...", returncode=0)
    with patch("sys.stdout", new_callable=MagicMock) as mock_stdout:
        ping_host("example.com")
    assert mock_run.called
    assert "success" in "".join([c[0][0] for c in mock_stdout.write.call_args_list]).lower()

@patch("socket.create_connection")
def test_check_connection_success(mock_conn):
    mock_conn.return_value = MagicMock()
    with patch("sys.stdout", new_callable=MagicMock):
        check_connection("example.com", 80)
    assert mock_conn.called

@patch("socket.create_connection")
def test_check_connection_fail(mock_conn):
    mock_conn.side_effect = socket.timeout("timeout")
    with patch("sys.stdout", new_callable=MagicMock) as mock_stdout:
        check_connection("example.com", 9999)
    output = "".join([c[0][0] for c in mock_stdout.write.call_args_list]).lower()
    assert "error" in output or "timeout" in output
