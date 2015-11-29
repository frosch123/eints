#!/usr/bin/env python3

import subprocess, re, os.path, sys, fcntl, getopt, datetime

# Connecting to eints
eints_base_url = "http://localhost:7080"

# Eints authentification
eints_login_file = "user.cfg"

# SVN credentials
svn_login = "translators"
commit_message = "-Update from Eints:\n"

# External tools
lang_sync_command = "lang_sync"
svn_command = "svn"

# Tempoary files
lock_file = "/tmp/eints.lock"
msg_file = "/tmp/eints.msg"



class FileLock:
    """
    Inter-process lock mechanism via exclusive file locking.
    """
    def __init__(self, name):
        self.name = name
        self.file = None

    def __enter__(self):
        assert self.file is None

        self.file = open(self.name, 'a')
        try:
            fcntl.flock(self.file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except:
            self.file.close()
            self.file = None
            raise
        self.file.truncate()
        self.file.write('pid:{} date:{:%Y-%m-%d %H:%M:%S}\n'.format(os.getpid(), datetime.datetime.now()))
        self.file.flush()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        assert self.file is not None

        os.remove(self.name)
        fcntl.flock(self.file, fcntl.LOCK_UN)
        self.file.close()

        self.file = None

        return False

def print_info(msg):
    """
    Print info message.

    @param msg: Message
    @type  msg: C{str}
    """

    print("[{:%Y-%m-%d %H:%M:%S}] {}".format(datetime.datetime.now(), msg))

is_update_lang = re.compile(r"\w+ +[\w\-/\\]+\.txt\Z")
is_modified_lang = re.compile(r"M +[\w\-/\\]+\.txt\Z")

def svn_status(working_copy):
    """
    Check whether SVN working copy is in a valid status,
    and whether there are modifies.

    A valid state means:
     - No untracked files.
     - No added files.
     - No removed files.
    All these alterations are not allowed to be performed by eintssvn.

    @param working_copy: Path to working copy.
    @type  working_copy: C{str}

    @return: Whether files are modified.
    @rtype:  C{bool}
    """

    msg = subprocess.check_output([svn_command, "status", "--non-interactive", working_copy], universal_newlines=True)
    modified = False
    for l in msg.splitlines():
        if len(l) == 0:
            continue
        if is_modified_lang.match(l):
            modified = True
        else:
            raise Exception("Invalid checkout status: {}".format(l))

    return modified

def svn_update(working_copy):
    """
    Update SVN working copy, and check for modifications.

    @param working_copy: Path to working copy.
    @type  working_copy: C{str}

    @return: Whether files were updated.
    @rtype:  C{bool}
    """

    if svn_status(working_copy):
        subprocess.check_call([svn_command, "revert", "--non-interactive", "-R", working_copy])

    msg = subprocess.check_output([svn_command, "update", "--non-interactive", working_copy], universal_newlines=True)
    for l in msg.splitlines():
        if is_update_lang.match(l):
            return True

    return False

def svn_commit(working_copy, msg_file):
    """
    Commit SVN working copy.

    @param working_copy: Path to working copy.
    @type  working_copy: C{str}

    @param msg_file: Path to file with commit message.
    @type  msg_file: C{str}
    """

    subprocess.check_call([svn_command, "commit", "--non-interactive", "--username", svn_login, "-F", msg_file, working_copy])

def eints_upload(working_copy, project_id):
    """
    Update base language and translations to Eints.

    @param working_copy: Path to working copy.
    @type  working_copy: C{str}

    @param project_id: Eints project Id.
    @type  project_id: C{str}
    """

    subprocess.check_call([lang_sync_command, "--user-password-file", eints_login_file, "--base-url", eints_base_url, "--lang-file-ext", ".txt",
                           "--project", project_id, "--lang-dir", working_copy, "--unstable-lang-dir", os.path.join(working_copy, "unfinished"),
                           "upload-base", "upload-translations"])

def eints_download(working_copy, project_id, credits_file):
    """
    Download translations from Eints.

    @param working_copy: Path to working copy.
    @type  working_copy: C{str}

    @param project_id: Eints project Id.
    @type  project_id: C{str}

    @param credits_file: File for translator credits.
    @type  credits_file: C{str}
    """

    subprocess.check_call([lang_sync_command, "--user-password-file", eints_login_file, "--base-url", eints_base_url, "--lang-file-ext", ".txt",
                           "--project", project_id, "--lang-dir", working_copy, "--unstable-lang-dir", os.path.join(working_copy, "unfinished"),
                           "--credits", credits_file, 
                           "download-translations"])



def update_eints_from_svn(working_copy, project_id, force):
    """
    Perform the complete operation from syncing Eints from the repository.

    @param working_copy: Path to working copy.
    @type  working_copy: C{str}

    @param project_id: Eints project Id.
    @type  project_id: C{str}

    @param force: Upload even if no changes.
    @type  force: C{bool}
    """

    with FileLock(lock_file):
        print_info("Check SVN")
        if svn_update(working_copy) or force:
            print_info("Upload translations")
            eints_upload(working_copy, project_id)
        print_info("Done")

def commit_eints_to_svn(working_copy, project_id, dry_run):
    """
    Perform the complete operation from commit Eints changes to the repository.

    @param working_copy: Path to working copy.
    @type  working_copy: C{str}

    @param project_id: Eints project Id.
    @type  project_id: C{str}

    @param dry_run: Do not commit, leave as modified.
    @type  dry_run: C{bool}
    """

    with FileLock(lock_file):
        # Upload first in any case.
        print_info("Update SVN")
        svn_update(working_copy)
        print_info("Upload/Merge translations")
        eints_upload(working_copy, project_id)
    
        print_info("Download translations")
        eints_download(working_copy, project_id, msg_file)
        if svn_status(working_copy):
            print_info("Commit SVN")
            # Assemble commit messge
            f = open(msg_file, 'r+', encoding = 'utf-8')
            cred = f.read()
            f.seek(0)
            f.truncate(0)
            f.write(commit_message)
            f.write(cred)
            f.close()

            if not dry_run:
                svn_commit(working_copy, msg_file)
        print_info("Done")



def run():
    """
    Run the program (it was started from the command line).
    """

    try:
        opts, args = getopt.getopt(sys.argv[1:], "h", ["help", "force", "dry-run", "project=", "working-copy="])
    except getopt.GetoptError as err:
        print("eintssvn: " + str(err) + " (try \"eintssvn --help\")")
        sys.exit(2)

    # Parse options
    force = False
    dry_run = False
    project_id = None
    working_copy = None
    for opt, val in opts:
        if opt in ('--help', '-h'):
            print("""\
eintssvn -- Synchronize language files between the SVN and Eints.

eintssvn <options> <operations>

with <options>:

--help
-h
    Get this help text.

--force
    See individual operations below

--dry-run
    See individual operations below

--project
    Eints project identifier

--working-copy
    Path to SVN working copy



and <operations>:

update-from-svn
    Update working copy and upload modifications.
    With --force upload even if SVN reported no modifications.

commit-to-svn
    Update working copy, merge and download translations from Eints, and commit.
    With --dry-run stop before committing and leave modifies in working copy.

""")
            sys.exit(0)

        if opt == "--force":
            force = True
            continue

        if opt == "--dry-run":
            dry_run = True
            continue

        if opt == "--project":
            if project_id:
                print("Duplicate --project option")
                sys.exit(2)
            project_id = val
            continue

        if opt == "--working-copy":
            if working_copy:
                print("Duplicate --working-copy option")
                sys.exit(2)
            working_copy = val
            continue

        raise ValueError("Unknown option {} encountered.".format(opt))

    # Parse operations
    do_update = False
    do_commit = False

    for arg in args:
        if arg == "update-from-svn":
            do_update = True
            continue

        if arg == "commit-to-svn":
            do_commit = True

            continue

        print("Unknown operation: {}".format(arg))
        sys.exit(2)

    # Check options
    if do_update or do_commit:
        if project_id is None:
            print("No --project specified")
            sys.exit(2)

        if working_copy is None:
            print("No --working-copy specified")
            sys.exit(2)

    # Execute operations
    if do_update:
        update_eints_from_svn(working_copy, project_id, force)

    if do_commit:
        commit_eints_to_svn(working_copy, project_id, dry_run)

    sys.exit(0)

if __name__ == '__main__':
    run()
