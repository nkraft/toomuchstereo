from collections import defaultdict
import hashlib
import itertools as it
import os
import sqlite3


# https://stackoverflow.com/a/3431838
def get_file_hash(file_path):
    hash_ = hashlib.blake2b()
    with open(file_path, 'rb') as file_:
        for chunk in iter(lambda: file_.read(4096), b''):
            hash_.update(chunk)
    return hash_.hexdigest()


def get_file_paths(root_dir, extensions):
    for dirpath, dirnames, filenames in os.walk(os.path.abspath(root_dir)):
        for filename in filenames:
            _, ext = os.path.splitext(filename)
            if (ext.lower() in extensions) or (len(extensions) == 0):
                yield os.path.join(dirpath, filename)


def get_path_hash(path):
    hash_ = hashlib.blake2b(os.path.abspath(path).encode())
    return hash_.hexdigest()


def get_image_extensions():
    return ['.bmp', '.gif', '.jpg', '.jpe', '.jpeg', '.png', '.tif', '.tiff']


def get_video_extensions():
    return ['.avi', '.mov', '.mp4', '.mpg', '.mkv', '.mts']


def get_hashes_table_name(name):
    return name + '_hashes'


def get_duplicates_table_name(name):
    return name + '_duplicates'


def create_hashes_table(connection, dir_path, name, get_extensions_func):
    hashes_table_name = get_hashes_table_name(name)
    cursor = connection.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='" + hashes_table_name + "'")
    exists = bool(cursor.fetchone())
    if not exists:
        print('Creating table: ' + hashes_table_name)
        cursor.execute('CREATE TABLE ' + hashes_table_name + ' (hash text, path text)')
        for file_path in get_file_paths(dir_path, set(get_extensions_func())):
            file_hash = get_file_hash(file_path)
            cursor.execute('INSERT INTO ' + hashes_table_name + ' VALUES (?,?)', (file_hash, file_path))
        connection.commit()


def create_duplicates_table(connection, name):
    duplicates_table_name = get_duplicates_table_name(name)
    reader = connection.cursor()
    reader.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='" + duplicates_table_name + "'")
    exists = bool(reader.fetchone())
    if not exists:
        print('Creating table: ' + duplicates_table_name)
        writer = connection.cursor()
        writer.execute('CREATE TABLE ' + duplicates_table_name + ' (hash text, dup_count integer)')
        reader.execute('SELECT hash, COUNT(*) as c FROM ' + get_hashes_table_name(name) + ' GROUP BY hash HAVING c > 1 ORDER BY c DESC')
        for (hash_, count) in reader:
            writer.execute('INSERT INTO ' + duplicates_table_name + ' VALUES (?,?)', (hash_, count))
        connection.commit()


def query(connection, name):
    dups_reader = connection.cursor()
    hashes_reader = connection.cursor()
    for (hash_, count) in dups_reader.execute('SELECT * FROM ' + get_duplicates_table_name(name)):
        for i, (path, ) in enumerate(hashes_reader.execute('SELECT path FROM ' + get_hashes_table_name(name) + ' WHERE hash=?', (hash_, ))):
            if i > 0:
                print('"' + path + '"')


def main(args):
    dir_path = '../../Google Drive'
    dir_path_hash = get_path_hash(dir_path)
    connection = sqlite3.connect(dir_path_hash + '.db')

    create_hashes_table(connection, dir_path, 'image', get_image_extensions)
    create_duplicates_table(connection, 'image')
    query(connection, 'image')

    #create_hashes_table(connection, dir_path, 'file', list)
    #create_duplicates_table(connection, 'file')
    #query(connection, 'file')

    connection.close()
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))

