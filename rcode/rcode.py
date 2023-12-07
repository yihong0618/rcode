#!/usr/bin/env python3
# MIT
# fork from https://github.com/chvolkmann/code-connect

import argparse
import os
import subprocess as sp
import time
from distutils.spawn import find_executable
from pathlib import Path
from os.path import expanduser
from typing import Iterable, List, NoReturn, Sequence, Tuple

from sshconf import read_ssh_config  # type: ignore

# IPC sockets will be filtered based when they were last accessed
# This gives an upper bound in seconds to the timestamps
DEFAULT_MAX_IDLE_TIME: int = 4 * 60 * 60


def fail(*msgs, retcode: int = 1) -> NoReturn:
    """Prints messages to stdout and exits the script."""
    for msg in msgs:
        print(msg)
    exit(retcode)


def is_socket_open(path: Path) -> bool:
    """Returns True if the UNIX socket exists and is currently listening."""
    try:
        proc = sp.run(
            ["socat", "-u", "OPEN:/dev/null", f"UNIX-CONNECT:{path.resolve()}"],
            stdout=sp.PIPE,
            stderr=sp.PIPE,
        )
        return proc.returncode == 0
    except:
        return False


def sort_by_access_timestamp(paths: Iterable[Path]) -> List[Tuple[float, Path]]:
    """Returns a list of tuples (last_accessed_ts, path) sorted by the former."""
    paths_list = [(p.stat().st_atime, p) for p in paths]
    paths_list = sorted(paths_list, reverse=True)
    return paths_list


def next_open_socket(socks: Sequence[Path]) -> Path:
    """Iterates over the list and returns the first socket that is listening."""
    try:
        return next((sock for sock in socks if is_socket_open(sock)))
    except StopIteration:
        fail(
            "Could not find an open VS Code IPC socket.",
            "",
            "Please make sure to connect to this machine with a standard "
            + "VS Code remote SSH session before using this tool.",
        )


def is_remote_vscode() -> bool:
    code_repos = Path.home().glob(".vscode-server/bin/*")
    return len(list(code_repos)) > 0 and os.getenv("SSH_CLIENT")


IS_REMOTE_VSCODE = is_remote_vscode()


def get_code_binary() -> Path:
    """Returns the path to the most recently accessed code executable."""

    # Every entry in ~/.vscode-server/bin corresponds to a commit id
    # Pick the most recent one
    code_repos = sort_by_access_timestamp(Path.home().glob(".vscode-server/bin/*"))
    if len(code_repos) == 0:
        fail(
            "No installation of VS Code Server detected!",
            "",
            "Please connect to this machine through a remote SSH session and try again.",
            "Afterwards there should exist a folder under ~/.vscode-server",
        )

    _, code_repo = code_repos[0]
    path = code_repo / "bin" / "code"
    if os.path.exists(path):
        return path
    return code_repo / "bin" / "remote-cli" / "code"


def get_ipc_socket(max_idle_time: int = DEFAULT_MAX_IDLE_TIME) -> Path:
    """Returns the path to the most recently accessed IPC socket."""

    # List all possible sockets for the current user
    # Some of these are obsolete and not actively listening anymore
    uid = os.getuid()
    socks = sort_by_access_timestamp(
        Path(f"/run/user/{uid}/").glob("vscode-ipc-*.sock")
    )

    # Only consider the ones that were active N seconds ago
    now = time.time()
    sock_list = [sock for ts, sock in socks if now - ts <= max_idle_time]

    # Find the first socket that is open, most recently accessed first
    return next_open_socket(sock_list)


def check_for_binaries() -> None:
    """Verifies that all required binaries are available in $PATH."""
    if not find_executable("socat"):
        fail('"socat" not found in $PATH, but is required for code-connect')


def run_remote(dir_name, max_idle_time: int = DEFAULT_MAX_IDLE_TIME) -> NoReturn:
    if not dir_name:
        raise Exception("need dir name here")
    # Fetch the path of the "code" executable
    # and determine an active IPC socket to use
    if IS_REMOTE_VSCODE:
        check_for_binaries()
        code_binary = get_code_binary()
        ipc_socket = get_ipc_socket(max_idle_time)

        args = [str(code_binary)]
        args.append(dir_name)
        os.environ["VSCODE_IPC_HOOK_CLI"] = str(ipc_socket)

        # run the "code" executable with the proper environment variable set
        # stdout/stderr remain connected to the current process
        proc = sp.run(args)
        # return the same exit code as the wrapped process
        exit(proc.returncode)


def run_loacl(
        dir_name,
        remote_name=None,
        is_latest=False,
        shortcut_name=None,
        open_shortcut_name=None,
):
    # run local to open remote
    rcode_home = Path.home() / ".rcode"
    ssh_remote = "vscode-remote://ssh-remote+{remote_name}{remote_dir}"
    rcode_used_list = []
    if os.path.exists(rcode_home):
        with open(rcode_home) as f:
            rcode_used_list = list(f.read().splitlines())
    if is_latest:
        if rcode_used_list:
            ssh_remote_latest = rcode_used_list[-1].split(",")[-1].strip()
            proc = sp.run(["code", "--folder-uri", ssh_remote_latest])
            exit(proc.returncode)
        else:
            print("Not use rcode before, just use it once")
            return
    if open_shortcut_name and rcode_used_list:
        for l in rcode_used_list:
            name, server = l.split(",")
            if open_shortcut_name.strip() == name.strip():
                proc = sp.run(["code", "--folder-uri", server.strip()])
                # then add it to the latest
                with open(rcode_home, "a") as f:
                    f.write(f"latest,{server}{str(os.linesep)}")
                exit(proc.returncode)
        else:
            raise Exception(f"no short_cut name in your added")

    sshs = read_ssh_config(expanduser("~/.ssh/config"))
    hosts = sshs.hosts()
    remote_name = remote_name
    if remote_name not in hosts:
        raise Exception("Please config your .ssh config to use this")
    dir_name = dir_name
    local_home_dir = expanduser("~")
    if dir_name.startswith(local_home_dir):
        user_name = sshs.host(remote_name).get("user", "root")
        # replace with the remote ~
        dir_name = str(dir_name).replace(local_home_dir, f"/home/{user_name}")
    ssh_remote = ssh_remote.format(remote_name=remote_name, remote_dir=dir_name)
    with open(rcode_home, "a") as f:
        if shortcut_name:
            f.write(f"{shortcut_name},{ssh_remote}{str(os.linesep)}")
        else:
            f.write(f"latest,{ssh_remote}{str(os.linesep)}")

    proc = sp.run(["code", "--folder-uri", ssh_remote])
    exit(proc.returncode)


def main():
    parser = argparse.ArgumentParser(
        # %(prog)s <host> <dir>
        usage="""
        rcode <host> <dir>
        """,
        description="""
        just rcode \'file\' like your VSCode \'code\' .
        but you should config your ~/.ssh/config first
        """
    )
    parser.add_argument("dir", help="dir_name", nargs="?")
    parser.add_argument("host", help="ssh hostname", nargs="?")
    parser.add_argument(
        "-l",
        "--latest",
        dest="is_latest",
        action="store_true",
        help="if is_latest",
    )
    parser.add_argument(
        "-sn",
        "--shortcut_name",
        dest="shortcut_name",
        help="add shortcut name to this",
        type=str,
        required=False,
    )
    parser.add_argument(
        "-os",
        "--open_shortcut",
        dest="open_shortcut",
        help="if ",
        type=str,
        required=False,
    )
    options = parser.parse_args()
    if IS_REMOTE_VSCODE:
        run_remote(options.dir)
    else:
        run_loacl(
            options.host,
            options.dir,
            is_latest=options.is_latest,
            shortcut_name=options.shortcut_name,
            open_shortcut_name=options.open_shortcut,
        )


if __name__ == "__main__":
    main()
