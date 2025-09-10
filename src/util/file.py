import os
import shutil


def write_file(filename, content):
    with open(filename, 'w') as f:
        f.write(content)


def read_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()


def remove_files_in(folder_path):
    if not os.path.exists(folder_path):
        return

    for root, dirs, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            os.remove(file_path)

        for dir in dirs:
            dir_path = os.path.join(root, dir)
            shutil.rmtree(dir_path)


def create_folders(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
