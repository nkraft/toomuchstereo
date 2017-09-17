import hashlib
import itertools as it
import os
import sqlite3


def get_file_paths(root_dir, extensions):
    for dirpath, dirnames, filenames in os.walk(os.path.abspath(root_dir)):
        for filename in filenames:
            _, ext = os.path.splitext(filename)
            if ext.lower() in extensions:
                yield os.path.join(dirpath, filename)


# https://stackoverflow.com/a/3431838
def get_hash(file_path):
    hash_ = hashlib.blake2b()
    with open(file_path, 'rb') as file_:
        for chunk in iter(lambda: file_.read(4096), b''):
            hash_.update(chunk)
    return hash_.hexdigest()


def get_image_extensions():
    return ['.bmp', '.gif', '.jpg', '.jpe', '.jpeg', '.png', '.tif', '.tiff']


def get_video_extensions():
    return ['.avi', '.mov', '.mp4', '.mpg', '.mkv', '.mts']


conn = sqlite3.connect('images.db')
c = conn.cursor()
c.execute('''CREATE TABLE images (path text, hash text)''')
for file_path in get_file_paths('../..', set(get_image_extensions())):
    file_hash = get_hash(file_path)
    c.execute('INSERT INTO images VALUES (?,?)', (file_path, file_hash))
conn.commit()
for row in c.execute('SELECT * FROM images'):
    print(row)
#for row in c.execute('SELECT path FROM images GROUP BY hash HAVING COUNT(*) > 1'):
    #print(row)
for row in c.execute('SELECT path, COUNT(*) as c FROM images GROUP BY hash HAVING c > 1 ORDER BY c DESC'):
    print(row)
conn.close()

