import argparse
import os.path
import sys
import inotify.adapters
from functools import partial


LOGGING_ENABLED = True
REPLACE_LOCATION = '<!-- HIT_COUNTER -->'


def main():
    parser = argparse.ArgumentParser(description='create a hit counter for your web page')
    parser.add_argument('page', type=str,
                        help='the web page you want to create a hit counter for')
    parser.add_argument('countfile', type=str,
                        help='a file to store the current hit count for the page')

    args       = parser.parse_args()
    page       = args.page
    count_file = args.countfile
    if validate_arguments(page, count_file) is False:
        sys.exit(-1)
    action = partial(on_file_read, count_file, page)
    watch(page, action)


def watch(page, action):
    dir = str.encode(get_directory_of_file(page))
    watched_page = page.split('/')[-1]
    i = inotify.adapters.Inotify()

    i.add_watch(dir)

    try:
        for event in i.event_gen():
            if event is not None:
                (header, type_names, watch_path, filename) = event
                if 'IN_OPEN' in type_names and filename == str.encode(watched_page):
                    action()
    finally:
        i.remove_watch(dir)


def on_file_read(count_file, html_page):
    count = update_count_file(count_file)
    update_html(html_page, count)


def update_count_file(path):
    with open(path, 'r') as f:
        try:
            existing = int(f.read())
        except ValueError:
            existing = 0
    with open(path, 'w') as f:
        f.write(str(existing + 1))
    return existing + 1


def update_html(path, count):
    with open(path, 'r') as f:
        existing = f.read()
    new_page = existing.split("\n")
    for i, line in enumerate(new_page):
        if line.startswith(REPLACE_LOCATION):
            new_page[i] = "{0} {1}".format(REPLACE_LOCATION, str(count))
    with open(path, 'w') as f:
        f.write("\n".join(new_page))


def validate_arguments(page, count_file):
    if file_can_be_accessed(page, 'r') is False:
        print("{0} could not be opened for reading - are you sure it's the right file?".format(page))
        return False
    if file_can_be_accessed(count_file, 'a+') is False:
        print("{0} could not be opened for writing - are you sure it's the right file?".format(count_file))
        return False
    return True


def get_directory_of_file(path):
    return os.path.abspath(os.path.join(path, os.pardir))


def file_can_be_accessed(path, mode):
    try:
        open(path, mode)
        return True
    except IOError:
        return False


def log(msg):
    if LOGGING_ENABLED is True:
        print(msg)


if __name__ == "__main__":
    count_file = './count_file'
    page = './page.html'
    action = partial(on_file_read, count_file, page)
    action()
