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

def add_files(files):
    for file in files:
        file_path = find_file(file)
        if file_path is None:
            print(f"File {file} does not exist.")
            return
        sha1 = hashed(file_path)
        dirname = sha1[:2]
        filename = sha1[2:]
        object_path = os.path.join(find_repo_root(os.getcwd()), 'objects', dirname)
        os.makedirs(object_path, exist_ok=True)
        compress_object(object_path, filename, file_path)
        write_index(sha1, file_path)

def find_all_files():
    root = os.path.dirname(find_repo_root(os.getcwd()))
    dir_list = os.listdir(root)
    files = []
    search_dir(files, root)
    return files
    
def search_dir(files, current):
    dir_list = os.listdir(current)
    for item in dir_list:
        if item == '.mgit':
            continue
        item_path = os.path.join(current, item)
        if os.path.isdir(item_path):
            search_dir(files, item_path)
        elif os.path.isfile(item):
            files.append(item)
        

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
    if ref.startswith('ref:'):
        return os.path.join(find_repo_root(os.getcwd()), ref.split(' ', 1)[1])
    return os.path.join(find_repo_root(os.getcwd()), "HEAD")
def read_object(commit_sha1):
    root_path = find_repo_root(os.getcwd())
    object_path = os.path.join(root_path, 'objects', commit_sha1[:2], commit_sha1[2:])
    if not os.path.exists(object_path):
        raise RuntimeError(f"Object {commit_sha1} not found")
    with open(object_path, 'rb') as f:
        compressed = f.read()
    return zlib.decompress(compressed)
def get_commit_info(commit_sha1):
    while commit_sha1:
        decompressed = read_object(commit_sha1)
        commit = decompressed.split(b'\0', 1)[1]
        lines = commit.decode().splitlines()
        print(f"Commit: {commit_sha1}")
        parent_sha1 = None
        for line in lines:
            if line.startswith("parent "):
                parent_sha1 = line.split(' ', 1)[1]
            elif line == "":
                continue
            else:
                print(line)
        print()
        commit_sha1 = parent_sha1
def read_index():
    root_path = find_repo_root(os.getcwd())
    index_path = os.path.join(root_path, 'Index')
    files = []
    with open(index_path, 'r') as f:
        lines = f.readlines()
        for line in lines:
            files.append(line.split(": ",1)[0])
    return files

def find_tree_hash(commit_sha1):
    decompressed = read_object(commit_sha1)
    commit = decompressed.split(b'\0', 1)[1]
    lines = commit.decode().splitlines()
    for line in lines:
        if line.startswith("tree "):
            return line.split(' ', 1)[1]
    return None
def restore_tree(root, tree):
    decompressed = read_object(tree)
    tree = decompressed.split(b'\0', 1)[1]
    i = 0
    while i < len(tree):
        mode_end = tree.find(b' ', i)
        name_end = tree.find(b'\0', mode_end)
        mode = tree[i:mode_end].decode()
        name = tree[mode_end+1:name_end].decode()
        sha = tree[name_end+1:name_end+21].hex()
        i = name_end + 21
        fullpath = os.path.join(root, name)
        if mode == "40000":
            os.makedirs(fullpath, exist_ok=True)
            restore_tree(fullpath, sha)
        else:
            blob_decompressed = read_object(sha)
            blob = blob_decompressed.split(b'\0', 1)[1]
            with open (fullpath, 'wb') as f:
                f.write(blob)