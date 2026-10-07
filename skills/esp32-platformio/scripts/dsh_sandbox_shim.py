"""DSH sandbox compatibility shim -- imported automatically via sitecustomize.

Why this exists
---------------
The DSH file sandbox grants write access to the workspace through an
*inheritable* capability ACE on the workspace directory.  Anything created
with the default (inherited) DACL therefore stays writable.

CPython's `tempfile.mkdtemp()` -- and any `os.mkdir(path, 0o700)` -- instead
asks Windows for an *explicit* DACL derived from the mode.  That explicit DACL
replaces the inherited one and drops the sandbox capability ACE, so the very
next write into the freshly created directory fails with:

    PermissionError: [Errno 13] Permission denied

This breaks pip, virtualenv bootstrap, and any tool that stages files through a
private temp directory.  Restoring the default mode keeps the inherited DACL
intact.  It is safe: on Windows a directory mode has no real meaning anyway.

The shim is a no-op on non-Windows platforms.
"""

import os as _os
import sys as _sys

if _sys.platform == "win32":
    _real_mkdir = _os.mkdir

    def _sandbox_safe_mkdir(path, mode=0o777, *args, **kwargs):
        # Always request the default mode so Windows keeps the inherited DACL.
        return _real_mkdir(path, 0o777, *args, **kwargs)

    _os.mkdir = _sandbox_safe_mkdir
