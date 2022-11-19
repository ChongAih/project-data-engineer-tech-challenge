import os


def get_config_folder_path():
    os.chdir(os.path.dirname(__file__))
    os.chdir('..')
    return os.path.join(os.getcwd(), "conf")


def get_resource_path():
    os.chdir(os.path.dirname(__file__))
    os.chdir('..')
    return os.path.join(os.getcwd(), "resource")


def get_resource_src_path():
    return os.path.join(get_resource_path(), "src")


def get_resource_dest_path():
    return os.path.join(get_resource_path(), "dest")


def get_config_file_path(config_filename: str):
    return os.path.join(get_config_folder_path(), config_filename)
