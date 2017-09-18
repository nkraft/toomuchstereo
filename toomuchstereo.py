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
            if ext.lower() in extensions:
                yield os.path.join(dirpath, filename)


def get_image_extensions():
    return ['.bmp', '.gif', '.jpg', '.jpe', '.jpeg', '.png', '.tif', '.tiff']


def get_path_hash(path):
    hash_ = hashlib.blake2b(os.path.abspath(path).encode())
    return hash_.hexdigest()


def get_video_extensions():
    return ['.avi', '.mov', '.mp4', '.mpg', '.mkv', '.mts']


def create_images_table(connection, dir_path):
    cursor = connection.cursor()
    cursor.execute("""SELECT name FROM sqlite_master
                      WHERE type='table' AND name='images'""")
    exists = bool(cursor.fetchone())
    if not exists:
        print('Creating images table')
        cursor.execute('CREATE TABLE images (hash text, path text)')
        for file_path in get_file_paths(dir_path, set(get_image_extensions())):
            file_hash = get_file_hash(file_path)
            cursor.execute('INSERT INTO images VALUES (?,?)', (file_hash, file_path))
        connection.commit()


def create_duplicate_images_table(connection):
    reader = connection.cursor()
    reader.execute("""SELECT name FROM sqlite_master
                      WHERE type='table' AND name='duplicate_images'""")
    exists = bool(reader.fetchone())
    if not exists:
        print('Creating duplicate images table')
        writer = connection.cursor()
        writer.execute('CREATE TABLE duplicate_images (hash text, dup_count integer)')
        reader.execute('''SELECT hash, COUNT(*) as c
                          FROM images
                          GROUP BY hash
                          HAVING c > 1
                          ORDER BY c DESC''')
        for (hash_, count) in reader:
            writer.execute('INSERT INTO duplicate_images VALUES (?,?)', (hash_, count))
        connection.commit()


def query(connection):
    dup_reader = connection.cursor()
    img_reader = connection.cursor()
    for (hash_, count) in dup_reader.execute('SELECT * FROM duplicate_images'):
        print(hash_)
        for (path, ) in img_reader.execute('SELECT path FROM images WHERE hash=?', (hash_, )):
            print('   ', path)


def main(args):
    dir_path = '../../Google Drive'
    dir_path_hash = get_path_hash(dir_path)
    connection = sqlite3.connect(dir_path_hash + '.db')
    create_images_table(connection, dir_path)
    create_duplicate_images_table(connection)
    #query(connection)
    connection.close()
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))

