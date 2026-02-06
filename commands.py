import os
import hashlib
import zlib
from datetime import datetime
from helpers import *

def init():
    filepath = os.path.join(os.getcwd(), '.mgit')
    if not os.path.exists(filepath):
        os.makedirs(filepath)
        initsial_repos(filepath)
    else:
        print("Repository already initialized.")

def add(files):
    print(f"Adding files: {', '.join(files)}")
    for file in files:
        file_path = find_file(file)
        if file_path == None:
            print(f"File {file} does not exist.")
            return
        sha1 = hashed(file_path)
        dirname = sha1[:2]
        filename = sha1[2:]
        object_path = os.path.join(find_repo_root(os.getcwd()), 'objects', dirname)
        os.makedirs(object_path, exist_ok=True)
        compress_object(object_path, filename, file_path)
        write_index(sha1, file_path)
def commit(message):
    tree_sha1 = create_tree()
    commit_content = get_content(tree_sha1, message)
    header = f"commit {len(commit_content)}\0".encode()
    full_content = header + commit_content
    sha = hashlib.sha1(full_content).hexdigest()
    dirname = sha[:2]
    filename = sha[2:]
    object_path = os.path.join(find_repo_root(os.getcwd()), 'objects', dirname)
    os.makedirs(object_path, exist_ok=True)
    compressed = zlib.compress(full_content)
    object_file = os.path.join(object_path, filename)
    if not os.path.exists(object_file):
        with open(object_file, 'wb') as f:
            f.write(compressed)
    ref_path = get_head_ref()
    os.makedirs(os.path.dirname(ref_path), exist_ok=True)
    with open(ref_path, 'w') as f:
        f.write(sha)
    clear_index()
    print(f"Committing with message: {message}")

def status():
    files = read_index()
    if len(files) == 0:
        print("No changes staged for commit")
    else:
        added_files = "\n".join(files)
        print(f"Changes to be commited\n (use unstage to remove this files from the staging area)\n {added_files}")

def unstage():
    clear_index()

def log():
    ref_path = get_head_ref()
    with open(ref_path, 'r') as f:
        commit_sha1 = f.read().strip()
    if not commit_sha1:
        print("Repository log: No commits yet.")
        return
    else:
        get_commit_info(commit_sha1)

def checkout(target):
    ref_path = get_head_ref()
    with open(ref_path, 'r') as f:
        commit_sha1 = f.read().strip()
    if target == commit_sha1:
        print(f"Already on {target}")
        return  
    else:
        tree_sha1 = find_tree_hash(target)
        root_path = os.path.dirname(find_repo_root(os.getcwd()))
        restore_tree(root_path, tree_sha1)
    root = find_repo_root(os.getcwd())
    with open(os.path.join(root, "HEAD"), "w") as f:
        f.write(target)
    print(f"Checking out to {target}...")

def restore_head():
    root = find_repo_root(os.getcwd())
    head_path = os.path.join(root, "HEAD")
    with open(head_path) as f:
        content = f.read().strip()
    if content.startswith('ref:'):
        return
    else:
        with open(head_path, 'w') as f:
            f.write('ref: refs/heads/main\n')