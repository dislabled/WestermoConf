"""scrapli_community.westermo.weos.sync_driver"""
from scrapli.driver import NetworkDriver
from time import sleep


def default_sync_on_open(conn: NetworkDriver) -> None:
    """
    Async westermo_weos default on_open callable

    Args:
        conn: NetworkDriver object

    Returns:
        N/A

    Raises:
        N/A

    """
    conn.acquire_priv(desired_priv=conn.default_desired_privilege_level)
    conn.send_command(command="interactive")
    # conn.send_command(command="set cli scripting-mode on")
    # conn.send_command(command="set cli pager off")


def default_sync_on_close(conn: NetworkDriver) -> None:
    """
    westermo_weos default on_close callable

    Args:
        conn: NetworkDriver object

    Returns:
        N/A

    Raises:
        N/A

    """
    conn.acquire_priv(desired_priv=conn.default_desired_privilege_level)
    conn.channel.write(channel_input="logout")
    conn.channel.send_return()
