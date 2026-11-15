"""Recognize Cloud's empty read-only anchor guards without allowing Git output."""
from pathlib import Path
import stat


def inside_repository(path):
    path=Path(path).resolve()
    for parent in (path,*path.parents):
        marker=parent/'.git'
        if not marker.exists() and not marker.is_symlink():continue
        # Managed Cloud reserves these exact anchors using empty, read-only
        # directories. They are not Git metadata. All other markers fail closed,
        # including gitdir files, symlinks, writable/filled guards and nested repos.
        if parent in (Path('/workspace'),Path('/tmp')) and not marker.is_symlink() and marker.is_dir():
            try:
                if not marker.stat().st_mode & (stat.S_IWUSR|stat.S_IWGRP|stat.S_IWOTH) and not any(marker.iterdir()):
                    continue
            except OSError:pass
        return True
    return False
