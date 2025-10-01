import glob
import os


def delete_files(folder: str, extensions: list[str]) -> None:
    for ext in extensions:
        files = glob.glob(os.path.join(folder, f'*.{ext}'))
        for file in files:
            try:
                os.remove(file)
                print(f'Deleted: {file}')
            except OSError as e:
                print(f'Error deleting {file}: {e}')


ROOT = os.path.dirname(os.path.realpath(__file__))
CY_PATH = os.path.join(ROOT, 'src', 'bnbpy', 'cython')
CY_PATH_PFSSP = os.path.join(ROOT, 'src', 'bnbprob', 'pfssp', 'cython')
CPP_PATH_PFSSP = os.path.join(ROOT, 'src', 'bnbprob', 'pfssp', 'cpp')
CY_PATH_PAFSSP = os.path.join(ROOT, 'src', 'bnbprob', 'pafssp', 'cython')
CPP_PATH_PAFSSP = os.path.join(ROOT, 'src', 'bnbprob', 'pafssp', 'cpp')


def main() -> None:
    # Define the folders
    cython_folders = [CY_PATH, CY_PATH_PFSSP, CY_PATH_PAFSSP]
    cpp_folders = [CPP_PATH_PFSSP, CPP_PATH_PAFSSP]

    # Define extensions to delete
    cython_extensions = ['cpp', 'pyd', 'so', 'html']
    cpp_extensions = ['pyd', 'so', 'html']

    # Delete files in "cython"
    for cy in cython_folders:
        if os.path.exists(cy):
            delete_files(cy, cython_extensions)
        else:
            print(f'Folder not found: {cy}')

    # Delete files in "cpp"
    for cpp in cpp_folders:
        if os.path.exists(cpp):
            delete_files(cpp, cpp_extensions)
        else:
            print(f'Folder not found: {cpp}')


if __name__ == '__main__':
    main()
