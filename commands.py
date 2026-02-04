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