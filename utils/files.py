import os, re
from typing import Iterable, Optional
from pathlib import Path


"""
===================================================================================
File Renaming
===================================================================================
"""


def rename_files_with_existing_index(
    target_prefix: str,
    new_prefix: str,
    target_dir: str,
    default_extension: str = "png",
):
    """
    Rename a list of files, will automatically

    Parameters
    ----------
    target_files : list
        _description_
    new_prefix : str
        _description_
    start_index : int
        _description_
    default_extension : str, optional
        _description_, by default "png"
    """
    start_index = max_frame_number(target_dir, new_prefix) + 1
    target_files = dumb_file_search(target_dir, target_prefix)
    print(target_files)
    for file in target_files:
        path = Path(file)
        file_name = path.name
        if "." in file_name:
            split_file = file_name.split(".")
            extension = split_file[-1]
        else:
            extension = default_extension
        parent_dir = path.parent
        new_name = f"{new_prefix}{start_index}.{extension}"
        new_path = os.path.join(parent_dir, new_name)
        print(new_path)
        os.rename(file, new_path)
        start_index += 1


"""
===================================================================================
File Searching
===================================================================================
"""


def dumb_file_search(source_dir: str, prefix: str) -> list:
    """
    Search a file based on a prefix. For example a prefix of "s" will return ["s1.png", "s2.png", etc.]
                                                 a prefix of "s_" will return ["s_1.png", "s_2.png", etc.]

    Parameters
    ----------
    source_dir : str
        Directory to search.
    prefix : str
        File name prefix to match.

    Returns
    -------
    list
        List of matching files.
    """
    paths = []
    files = os.listdir(source_dir)
    for file in files:
        if prefix in file:
            path = os.path.join(source_dir, file)
            paths.append(path)
    return paths


"""
    ===================================================================================
    File Utilities
    ===================================================================================
    """


def max_frame_number(
    dirpath: str,
    prefix: str,
    divider: str = "",
    exts: Iterable[str] = (".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"),
) -> int:
    """
    Scan a directory (non-recursive) and return the maximum integer that follows `prefix`
    in the filename stem. Ignores files with other prefixes or extensions.
    """
    if isinstance(dirpath, str):
        dirpath = Path(dirpath)

    exts = {e.lower() for e in exts}
    if divider:
        pattern = rf"^{re.escape(prefix)}{divider}(\d+)$"
    else:
        pattern = rf"^{re.escape(prefix)}(\d+)$"

    rx = re.compile(pattern)
    max_n: Optional[int] = None

    for p in dirpath.iterdir():
        if not p.is_file():
            continue
        if p.suffix.lower() not in exts:
            continue
        m = rx.match(p.stem)
        if not m:
            continue
        n = int(m.group(1))
        if max_n is None or n > max_n:
            max_n = n

    return max_n or 0
