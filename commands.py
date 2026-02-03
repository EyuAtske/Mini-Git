import os
import hashlib

def init():
    filepath = os.path.join(os.getcwd(), '.mgit')
    if not os.path.exists(filepath):
        os.makedirs(filepath)
        initsial_repos(filepath)
    else:
        print("Repository already initialized.")

def add(files):
    for file in files:
        if not os.path.exists(file):
            print(f"File {file} does not exist.")
            return
        size = os.path.getsize(file)
        hasher = hashlib.sha1()
        header = f"blob {size}\0".encode()
        hasher.update(header)
        for chunk in read_bytes(file):
            hasher.update(chunk)
        sha1 = hasher.hexdigest()
        dirname = sha1[:2]
        filename = sha1[2:]
        object_path = os.path.join(find_repo_root(os.getcwd()), 'objects', dirname)
    print(f"Adding files: {', '.join(files)}")

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
        if os.path.isdir(os.path.join(current_path, '.mgit')){
            return os.path.join(current_path, '.mgit');
        }
        parent = os.path.dirname(current_path)
        if parent = current_path:
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