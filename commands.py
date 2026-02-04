import os
import hashlib
import zlib

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
    create_tree()
def commit(message):
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
            return ''
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
    index_path = os.path.join(root_path, 'Index')
    entry = f'{file}: {sha1}\n'
    with open(index_path, 'r') as f:
        existing_lines = set(f.readlines())
    if entry not in existing_lines:
        with open(index_path, 'a') as f:
            f.write(entry)

def find_file(file):
    if os.path.exists(file):
        return file
    return search_in_repo(file, os.getcwd())

def search_in_repo(file, current_path):
    dir_list = os.listdir(current_path)
    for item in dir_list:
        item_path = os.path.join(current_path, item)
        if os.path.isdir(item_path):
            path = item
            result = search_in_repo(file, item_path)
            if result != None:
                return path + '/' + result
        elif item == file:
            return item
    return None
def create_tree():
    root_path = find_repo_root(os.getcwd())
    index_path = os.path.join(root_path, 'Index')
    entities = []
    with open(index_path, 'r') as f:
        lines = f.readlines()
        for line in lines:
            files = line.split(': ')
            create_entities(entities, files[0], files[1])
            
def create_entities(entities, file, sha1):
    path_parts = file.split('/')
    if len(path_parts) == 1:
        entities.append(("100644", file, sha1))
        tree_hash(("100644", file, sha1))
    else:
        create_subtree(entities, path_parts, sha1)

def create_subtree(entities, path_parts, sha1):
    dir_name = path_parts[0]
    remaining_parts = path_parts[1:]
    subtree = []
    if len(remaining_parts) == 1:
        subtree.append(("100644", remaining_parts[0], sha1))
    else:
        create_subtree(subtree, remaining_parts, sha1)
    subtree_sha1 = tree_hash(subtree)
    entities.append(("40000", dir_name, subtree_sha1))
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