import sys, os, time
import requests


def download_file(url, file_name=None):
    """Downloads file from url and stores it as 'file_name' if given"""
    try:
        r = requests.get(url)
        # r.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(e)
        # raise Systemexit(e)
    else:
        if file_name is None:
            file_name = os.path.basename(url)

        with open(file_name, 'wb') as f:
            f.write(r.content)


# Update File if Necessary
def update_file(file_url, use_file_name=None, mtime=1, force=False, verbose=False):
    """Checks if a file exists on path, if not or if older than mtime
    (days, fraction possible), it downloads it from the url.
    If no file_name is given it uses the name on url.
    """
    if use_file_name is None:
        print('\nNo file Name given, using url basename. And returning its value')
        file_name = os.path.basename(file_url)
    else:
        file_name = use_file_name

    if os.path.exists(file_name):
        if verbose:
            print('\nFile already exists')

        time_diff = (time.time() - os.path.getmtime(file_name)) / (3600*24)

        if time_diff >= mtime or force:
            if verbose:
                print('\nLocal version older than required. Downloading from url...')

            download_file(file_url, file_name)
        else:
            print(f'\nThe date of local file {file_name} is within required timespan'
                  f'of {mtime} days. Not downloading')
    else:
        download_file(file_url, file_name)

    if use_file_name is None:
        return file_name

# command line input
def input_integer(default=0, message='Enter an option (integer) [q to quit]:'):
    """Enter integers until quiting is desired.
    If only enter is pressed the default value is used"""
    while True:

        n = input(f'\n{message}')
        if n == 'q':
            sys.exit(0)

        elif n == '':
            print(f'No pick, using default value {default}')
            return default

        try:
            n = int(n)
            return n

        except ValueError:
            print('Not a valid input')
