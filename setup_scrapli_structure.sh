#!/bin/bash

# setup_scrapli_structure.sh
# Script to properly restructure the westermo scrapli community platform

set -e  # Exit on any error

echo "Setting up proper scrapli_community package structure..."

# Create the directory structure
echo "Creating directories..."
mkdir -p scrapli_community/westermo/weos

# Create scrapli_community/__init__.py
echo "Creating scrapli_community/__init__.py..."
cat > scrapli_community/__init__.py << 'EOF'
"""Scrapli community platforms"""
EOF

# Create scrapli_community/westermo/__init__.py  
echo "Creating scrapli_community/westermo/__init__.py..."
cat > scrapli_community/westermo/__init__.py << 'EOF'
"""scrapli_community.westermo"""
EOF

# Create scrapli_community/westermo/weos/__init__.py
echo "Creating scrapli_community/westermo/weos/__init__.py..."
cat > scrapli_community/westermo/weos/__init__.py << 'EOF'
"""scrapli_community.westermo.weos"""
from scrapli_community.westermo.weos.westermo_weos import SCRAPLI_PLATFORM

__all__ = ("SCRAPLI_PLATFORM",)
EOF

# Copy and update westermo_weos.py with correct imports
echo "Creating scrapli_community/westermo/weos/westermo_weos.py..."
cat > scrapli_community/westermo/weos/westermo_weos.py << 'EOF'
"""scrapli_community.westermo.weos.westermo_weos"""

from scrapli.driver.network.base_driver import PrivilegeLevel
from scrapli_community.westermo.weos.async_driver import (
    default_async_on_close,
    default_async_on_open,
)
from scrapli_community.westermo.weos.sync_driver import default_sync_on_close, default_sync_on_open

DEFAULT_PRIVILEGE_LEVELS = {
    "exec": (
        PrivilegeLevel(
            pattern=r"^[\w]*:\/#>",
            name="exec",
            previous_priv="",
            deescalate="",
            escalate="",
            escalate_auth=False,
            escalate_prompt="",
        )
    ),
    "configuration": (
        PrivilegeLevel(
            pattern=r"\w+:\/config\/(?:[\w-]+\/)*#>\s*",
            name="configuration",
            previous_priv="exec",
            deescalate="leave",
            escalate="configure",
            escalate_auth=False,
            escalate_prompt="",
        )
    ),
}

SCRAPLI_PLATFORM = {
    "driver_type": "network",
    "defaults": {
        "privilege_levels": DEFAULT_PRIVILEGE_LEVELS,
        "default_desired_privilege_level": "exec",
        "sync_on_open": default_sync_on_open,
        "async_on_open": default_async_on_open,
        "sync_on_close": default_sync_on_close,
        "async_on_close": default_async_on_close,
        "failed_when_contains": [
            "not found.",
        ],
        "textfsm_platform": "",
        "genie_platform": "",
    },
}
EOF

# Create sync_driver.py
echo "Creating scrapli_community/westermo/weos/sync_driver.py..."
cat > scrapli_community/westermo/weos/sync_driver.py << 'EOF'
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
EOF

# Create async_driver.py
echo "Creating scrapli_community/westermo/weos/async_driver.py..."
cat > scrapli_community/westermo/weos/async_driver.py << 'EOF'
"""scrapli_community.westermo.weos.async_driver"""
from scrapli.driver import AsyncNetworkDriver


async def default_async_on_open(conn: AsyncNetworkDriver) -> None:
    """
    Async westermo_weos default on_open callable

    Args:
        conn: NetworkDriver object

    Returns:
        N/A

    Raises:
        N/A

    """
    await conn.acquire_priv(desired_priv=conn.default_desired_privilege_level)


async def default_async_on_close(conn: AsyncNetworkDriver) -> None:
    """
    Async westermo_weos default on_close callable

    Args:
        conn: NetworkDriver object

    Returns:
        N/A

    Raises:
        N/A

    """
    await conn.acquire_priv(desired_priv=conn.default_desired_privilege_level)
    conn.channel.write(channel_input="logout")
    conn.channel.send_return()
EOF

# Note: We're preserving the old westermo directory for safety
# You can manually remove it later once you've confirmed everything works:
# rm -rf westermo/
if [ -d "westermo" ]; then
    echo "⚠️  Note: Old westermo/ directory still exists and can be safely removed later"
    echo "   Once you've confirmed everything works, you can run: rm -rf westermo/"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Package structure created:"
echo "scrapli_community/"
echo "├── __init__.py"
echo "└── westermo/"
echo "    ├── __init__.py"
echo "    └── weos/"
echo "        ├── __init__.py"
echo "        ├── westermo_weos.py"
echo "        ├── sync_driver.py"
echo "        └── async_driver.py"
echo ""
echo "You can now run your main.py script - Scrapli should find the westermo_weos platform automatically!"
EOF

