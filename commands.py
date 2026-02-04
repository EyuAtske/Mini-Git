import os
import hashlib
import zlib
from datetime import datetime

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
    print("Repository status: All files are up to date.")

def log():
    print("Repository log: No commits yet.")

def checkout(target):
    print(f"Checking out to {target}...")

def initsial_repos(path):
    os.makedirs(os.path.join(path, 'objects'), exist_ok=True)
    os.makedirs(os.path.join(path, 'refs', 'heads'), exist_ok=True)
    open(os.path.join(path, 'Index'), 'w').close()
    with open(os.path.join(path, 'HEAD'), 'w') as f:
        f.write('ref: refs/heads/main\n')
    open(os.path.join(path, 'refs', 'heads', 'main'), 'w').close()
def find_repo_root(start_path):
    current_path = start_path
    while True:
        if os.path.isdir(os.path.join(current_path, '.mgit')):
            return os.path.join(current_path, '.mgit')
        parent = os.path.dirname(current_path)
        if parent == current_path:
            print("NO mgit repository")
            raise RuntimeError("Not inside an mgit repository")
        current_path = parent
def read_bytes(file_path):
    with open(file_path, 'rb') as f:
        while True:
            data = f.read(8192)
            if not data:
                break
            yield data
def hashed(file):
    size = os.path.getsize(file)
    hasher = hashlib.sha1()
    header = f"blob {size}\0".encode()
    hasher.update(header)
    for chunk in read_bytes(file):
        hasher.update(chunk)
    return hasher.hexdigest()
def compress_object(object_path, filename, file):
    size = os.path.getsize(file)
    header = f"blob {size}\0".encode()
    raw_object = header + b''.join(read_bytes(file))
    compressed = zlib.compress(raw_object)
    object_file = os.path.join(object_path, filename)
    if not os.path.exists(object_file):
        with open(object_file, 'wb') as f:
            f.write(compressed)
def write_index(sha1, file):
    root_path = find_repo_root(os.getcwd())
    repo_root = os.path.dirname(root_path)
    rel_path = os.path.relpath(file, repo_root)
    index_path = os.path.join(root_path, 'Index')
    entry = f'{rel_path}: {sha1}\n'
    entities = {}
    with open(index_path, 'r') as f:
        lines = f.readlines()
        for line in lines:
            p, s = line.strip().split(': ')
            entities[p] = s
    entities[rel_path] = sha1
    with open(index_path, 'w') as f:
        for p, s in entities.items():
            f.write(f'{p}: {s}\n')

def clear_index():
    root_path = find_repo_root(os.getcwd())
    index_path = os.path.join(root_path, 'Index')
    open(index_path, 'w').close()
def find_file(file):
    if os.path.exists(file):
        return os.path.abspath(file)
    return search_in_repo(file, os.getcwd())

def search_in_repo(file, current_path):
    dir_list = os.listdir(current_path)
    for item in dir_list:
        if item == '.mgit':
            continue
        item_path = os.path.join(current_path, item)
        if os.path.isdir(item_path):
            path = item
            result = search_in_repo(file, item_path)
            if result != None:
                return os.path.abspath(os.path.join(path, result))
        elif item == file:
            return os.path.abspath(item_path)
    return None
def create_tree():
    root = {}
    root_path = find_repo_root(os.getcwd())
    index_path = os.path.join(root_path, 'Index')
    with open(index_path, 'r') as f:
        lines = f.readlines()
        for line in lines:
            path, sha1 = line.strip().split(': ')
            add_path(root, path.split('/'), sha1)
    return write_tree(root)
            
def add_path(tree, file, sha1):
    if len(file) == 1:
        tree[file[0]] = sha1
        return
    dirname = file[0]
    if dirname not in tree:
        tree[dirname] = {}
    add_path(tree[dirname], file[1:], sha1)


def write_tree(tree):
    entities = []
    for name, value in sorted(tree.items()):
        if isinstance(value, dict):
            subtree_sha1 = write_tree(value)
            entities.append(("40000", name, subtree_sha1))
        else:
            entities.append(("100644", name, value))
    return tree_hash(entities)
    
def tree_hash(entities):
    tree_content = b''
    for mode, name, sha1 in entities:
        tree_content += f"{mode} {name}\0".encode() + bytes.fromhex(sha1)
    header = f"tree {len(tree_content)}\0".encode()
    full_content = header + tree_content
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
    return sha  
def get_content(tree_sha1, message):
    lines = []
    lines.append(f"tree {tree_sha1}")
    parent = get_head()
    if parent:
        lines.append(f"parent {parent}")
    timestamp = int(datetime.now().timestamp())
    lines.append(f"time {timestamp}")
    lines.append("")
    lines.append(message)
    return "\n".join(lines).encode()
def get_head():
    head_path = os.path.join(find_repo_root(os.getcwd()), "HEAD")
    with open(head_path, 'r') as f:
        ref = f.read().strip()
    if ref.startswith('ref:'):
        ref_path = ref.split(' ', 1)[1]
        full_path = os.path.join(find_repo_root(os.getcwd()), ref_path)
        if os.path.exists(full_path):
            with open(full_path, 'r') as f:
                return f.read().strip()
        return None
    return ref
def get_head_ref():
    head_path = os.path.join(find_repo_root(os.getcwd()), "HEAD")
    with open(head_path) as f:
        ref = f.read().strip()
    return os.path.join(find_repo_root(os.getcwd()), ref.split(' ', 1)[1])