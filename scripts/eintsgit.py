#!/usr/bin/env python3

import subprocess, re, os, os.path, sys, fcntl, getopt, datetime

# Connecting to eints
eints_base_url = "http://localhost:8000"

# Eints authentification
eints_login_file = "user.cfg"

# Commit credentials
commit_user = "translator@openttd.org"
commit_message = "Update: Translations\n"

# Source structure
lang_dir = "src/lang"
git_remote = "origin"
git_branch = "master"
git_remote_branch = git_remote + "/" + git_branch

# External tools
lang_sync_command = "./lang_sync"
git_command = "git"

# Temporary files
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

is_modified_lang = re.compile(r" M " + lang_dir + r"/[\w\-/\\]+\.txt\Z")

def git_status():
    """
    Check whether working copy is in a valid status,
    and whether there are modifies.

    A valid state means:
     - No untracked files.
     - No added files.
     - No removed files.
    All these alterations are not allowed to be performed by eintsgit.

    @return: Whether files are modified.
    @rtype:  C{bool}
    """

    msg = subprocess.check_output([git_command, "status", "-s"], universal_newlines=True)
    modified = False
    for l in msg.splitlines():
        if len(l) == 0:
            continue
        if is_modified_lang.match(l):
            modified = True
        else:
            raise Exception("Invalid checkout status: {}".format(l))

    return modified

def git_pull():
    """
    Update working copy, and revert all modifications.

    @return: Whether files were updated.
    @rtype:  C{bool}
    """

    subprocess.check_call([git_command, "fetch", git_remote])
    subprocess.check_call([git_command, "clean", "-f", os.environ.get("GIT_WORK_TREE")])
    changes = subprocess.check_output([git_command, "diff", "--name-only", "HEAD.." + git_remote_branch], universal_newlines=True)
    subprocess.check_call([git_command, "reset", "--hard", git_remote_branch])

    for l in changes.splitlines():
        if l.startswith(lang_dir) >= 0:
            return True

    return False

def git_push(lang_dir, msg_file, dry_run):
    """
    Commit and push working copy.

    @param lang_dir: Path to lang directory.
    @type  lang_dir: C{str}

    @param msg_file: Path to file with commit message.
    @type  msg_file: C{str}

    @param dry_run: Do not push
    @type  dry_run: C{bool}
    """

    subprocess.check_call([git_command, "add", lang_dir])
    subprocess.check_call([git_command, "commit", "--author", commit_user, "-F", msg_file])
    if not dry_run:
        subprocess.check_call([git_command, "push"])

def eints_upload(lang_dir, project_id):
    """
    Update base language and translations to Eints.

    @param lang_dir: Path to lang directory.
    @type  lang_dir: C{str}

    @param project_id: Eints project Id.
    @type  project_id: C{str}
    """

    subprocess.check_call([lang_sync_command, "--user-password-file", eints_login_file, "--base-url", eints_base_url, "--lang-file-ext", ".txt",
                           "--project", project_id, "--lang-dir", lang_dir, "--unstable-lang-dir", os.path.join(lang_dir, "unfinished"),
                           "upload-base", "upload-translations"])

def eints_download(lang_dir, project_id, credits_file):
    """
    Download translations from Eints.

    @param lang_dir: Path to lang directory.
    @type  lang_dir: C{str}

    @param project_id: Eints project Id.
    @type  project_id: C{str}

    @param credits_file: File for translator credits.
    @type  credits_file: C{str}
    """

    subprocess.check_call([lang_sync_command, "--user-password-file", eints_login_file, "--base-url", eints_base_url, "--lang-file-ext", ".txt",
                           "--project", project_id, "--lang-dir", lang_dir, "--unstable-lang-dir", os.path.join(lang_dir, "unfinished"),
                           "--credits", credits_file, 
                           "download-translations"])



def update_eints_from_git(lang_dir, project_id, force):
    """
    Perform the complete operation from syncing Eints from the repository.

    @param lang_dir: Path to lang directory.
    @type  lang_dir: C{str}

    @param project_id: Eints project Id.
    @type  project_id: C{str}

    @param force: Upload even if no changes.
    @type  force: C{bool}
    """

    with FileLock(lock_file):
        print_info("Check updates from git")
        if git_pull() or force:
            print_info("Upload translations")
            eints_upload(lang_dir, project_id)
        print_info("Done")

def commit_eints_to_git(lang_dir, project_id, dry_run):
    """
    Perform the complete operation from commit Eints changes to the repository.

    @param lang_dir: Path to lang directory.
    @type  lang_dir: C{str}

    @param project_id: Eints project Id.
    @type  project_id: C{str}

    @param dry_run: Do not commit, leave as modified.
    @type  dry_run: C{bool}
    """

    with FileLock(lock_file):
        # Upload first in any case.
        print_info("Update from git")
        git_pull()
        print_info("Upload/Merge translations")
        eints_upload(lang_dir, project_id)
    
        print_info("Download translations")
        eints_download(lang_dir, project_id, msg_file)
        if git_status():
            print_info("Commit changes")
            # Assemble commit messge
            f = open(msg_file, 'r+', encoding = 'utf-8')
            cred = f.read()
            f.seek(0)
            f.truncate(0)
            f.write(commit_message)
            f.write(cred)
            f.close()

            git_push(lang_dir, msg_file, dry_run)
        print_info("Done")



def run():
    """
    Run the program (it was started from the command line).
    """

    try:
        opts, args = getopt.getopt(sys.argv[1:], "h", ["help", "force", "dry-run", "project=", "working-copy="])
    except getopt.GetoptError as err:
        print("eintsgit: " + str(err) + " (try \"eintsgit --help\")")
        sys.exit(2)

    # Parse options
    force = False
    dry_run = False
    project_id = None
    working_copy = None
    for opt, val in opts:
        if opt in ('--help', '-h'):
            print("""\
eintsgit -- Synchronize language files between git and Eints.

eintsgit <options> <operations>

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
    Path to git working copy



and <operations>:

update-from-git
    Update working copy and upload modifications.
    With --force upload even if git reported no modifications.

commit-to-git
    Update working copy, merge and download translations from Eints, commit and push.
    With --dry-run stop before pushing and leave commits local.

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
        if arg == "update-from-git":
            do_update = True
            continue

        if arg == "commit-to-git":
            do_commit = True

            continue

        print("Unknown operation: {}".format(arg))
        sys.exit(2)

    # Check options
    if do_update or do_commit:
        if project_id is None:
            print("No --project specified")
            sys.exit(2)

        if working_copy:
            working_copy = os.path.abspath(working_copy)
            os.environ["GIT_WORK_TREE"] = working_copy
            os.environ["GIT_DIR"] = os.path.join(working_copy, ".git")
        else:
            print("No --working-copy specified")
            sys.exit(2)

    # Execute operations
    if do_update:
        update_eints_from_git(os.path.join(working_copy, lang_dir), project_id, force)

    if do_commit:
        commit_eints_to_git(os.path.join(working_copy, lang_dir), project_id, dry_run)

    sys.exit(0)

if __name__ == '__main__':
    run()
