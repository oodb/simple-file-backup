#!/usr/bin/python3

from datetime import datetime, timedelta
from pathlib import Path
import shutil
import sys
from typing import Union

# syntax cron (tous les jours à 10h)
# 0 10 * * * /Users/olivier.debbah/code/backup.py

FILE_MATCHES = {
    'notes_todo': {
        'path': '/Users/olivier.debbah/notes_todo/notes_todo.txt',
        'backup_root': 'notes_todo',
    },
    'sql': {
        'path': '/Users/olivier.debbah/code/misc.sql',
        'backup_root': 'misc.sql',
    },
}

class FileToBackup:
    def __init__(self, file_info: Union[str, dict]):
        if isinstance(file_info, dict):
            self.path = Path(file_info['path'])
            self.backup_root = file_info['backup_root']
        else:
            self.path = Path(file_info)
            self.backup_root = self.path.name

    def backup(self, force: bool = False) -> str:
        latest_backup = self.get_latest_backup()
        lb_date = latest_backup['date']
        now = datetime.now()

        # monday or more than a week since last backup or force
        if datetime.today().isoweekday() == 1 \
        or lb_date is None \
        or (now - lb_date) > timedelta(days=7) \
        or force:
            creation_path = self.make_backup_path()
            shutil.copyfile(self.path, creation_path)
            return creation_path
        else:
            return 'PASSED'

    def get_latest_backup(self) -> Union[dict, None]:
        backup: Path = None
        backup_date: datetime = None
        for f in (
                ff for ff in Path(self.path.parent).iterdir()
                if ff.name.startswith(self.path.stem)
                and ff.name.endswith(self.path.suffix)
                and ff.name != self.path.name
        ):
            d = datetime.fromtimestamp(f.stat().st_ctime)
            if backup is None or d > backup_date:
                backup = f
                backup_date = d
        return {'file': backup, 'date': backup_date} if backup else None

    def make_backup_path(self) -> str:
        now = datetime.now()
        return f'{self.path.parent}/{self.backup_root}_sauv_{now.year:04d}-{now.month:02d}-{now.day:02d}{self.path.suffix}'

def test_make_backup_path() -> None:
    now = datetime.now()
    file = FileToBackup("/home/test/file.txt")
    bkup_path = file.make_backup_path()
    print(f"BACKUP PATH FOR '{file.path}': '{bkup_path}'")
    assert bkup_path == f"/home/test/file.txt_sauv_{now.year:04d}-{now.month:02d}-{now.day:02d}.txt"
    #
    file = FileToBackup({
        "path": "/home/test/file.txt",
        "backup_root": "file",
    })
    bkup_path = file.make_backup_path()
    print(f"BACKUP PATH FOR '{file.path}': '{bkup_path}'")
    assert bkup_path == f"/home/test/file_sauv_{now.year:04d}-{now.month:02d}-{now.day:02d}.txt"


if __name__ == '__main__':
    from argparse import ArgumentParser
    argparser = ArgumentParser("Personal File Backup")
    argparser.add_argument("-p", "--path") # optional because of test arg
    argparser.add_argument("-f", "--force", action="store_true")
    argparser.add_argument("-t", "--test", action="store_true")
    args = argparser.parse_args()

    # case: tests
    if args.test:
        test_make_backup_path()
        sys.exit("TEST END")

    # case: no arg, backup all
    if args.path is None:
        print(f"default - try to backup all ({', '.join(FILE_MATCHES.keys())})")
        for file_info in FILE_MATCHES.values():
            fb =FileToBackup(file_info)
            print(fb.make_backup_path())
            fb.backup(args.force)
        sys.exit()

    # case: specific unknown path
    if args.path not in FILE_MATCHES:
        file = FileToBackup(args.path)
        if file.path.is_file():                   # direct file path given
            backup_root = file.path.name
            sys.exit(FileToBackup(args.path).backup(args.force))
        sys.exit(f'ERROR: unknown file "{args.path}"')

    # case: given name is in FILE_MATCHES
    bk_file = FileToBackup(FILE_MATCHES[args.path]).backup(args.force)
    sys.exit(bk_file)
