import os.path

def collect_paths(dir_name: str) -> list:
    """
    This is a function that estracts all paths and converts their filenames into a string
    """
    paths, names = [], []
    # Пути к файлам
    for address, _, files in os.walk(dir_name):
        for name in files:
                paths.append(os.path.join(address, name))
                names.append(name)
    names = ', '.join(names)
    if names == '':
         names = '0 files'
    return paths, names