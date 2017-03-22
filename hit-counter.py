import argparse
import os.path
import sys
import inotify.adapters


LOGGING_ENABLED = True


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
    watch(page, on_file_read)


def watch(page, action):
    log(page)
    log(action())
    dir = str.encode(get_directory_of_file(page))
    log(dir)
    i = inotify.adapters.Inotify()

    i.add_watch(dir)

    try:
        for event in i.event_gen():
            if event is not None:
                (header, type_names, watch_path, filename) = event
                if 'IN_READ' in type_names and filename == page:
                    action()
                log("WD=(%d) MASK=(%d) COOKIE=(%d) LEN=(%d) MASK->NAMES=%s WATCH-PATH=[%s] FILENAME=[%s]" %
                    (header.wd, header.mask, header.cookie, header.len, type_names,
                     watch_path.decode('utf-8'), filename.decode('utf-8')))
    finally:
        i.remove_watch(dir)


def on_file_read():
    log('file was read')


def validate_arguments(page, count_file):
    if file_can_be_accessed(page, 'r') is False:
        print("{0} could not be opened for reading - are you sure it's the right file?".format(page))
        return False
    if file_can_be_accessed(count_file, 'w+') is False:
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
    main()
