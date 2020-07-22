__author__ = "Reggy Tjitradi with support from Howard and Ramon"

import logging
import time
import signal
import argparse
import sys

from os import listdir
from os.path import isfile, join, splitext
from collections import defaultdict

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s:%(funcName)s:%(levelname)s:%(message)s')
# file_handler = logging.FileHandler('dirwatcher.log')
# file_handler.setFormatter(formatter)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)
# logger.addHandler(file_handler)

# Global Variables
exit_flag = False
banner_text = '\n' + '-' * 30 + '\n'


def signal_handler(sig_num, frame):
    """handler for system singals"""
    global exit_flag
    logger.warning('Received ' + signal.Signals(sig_num).name)
    exit_flag = True


def detect_added_files(files_dict, only_files, file_ext):
    """Loops through files list and checks to see if any
    new files that match extension exist.  If so adds them
    to files_dict."""
    for file in only_files:
        # splits file into name and extension
        filename, file_extension = splitext(file)
        if file_extension == file_ext:
            if file not in files_dict.keys():
                logger.info('New File detected : {0}'.format(file))
                files_dict[file] = 0
    return files_dict


def detect_removed_files(files_dict, only_files):
    """Loops through  dictionary and compares it to files
    currently in directory.  If a dictionary item is not in files
    list adds file to be removed."""
    files_to_remove = []
    for file in files_dict.keys():
        if file not in only_files:
            logger.info('Deleted File detected : {0}'.format(file))
            files_to_remove.append(file)
    for file in files_to_remove:
        del files_dict[file]
    return files_dict


def read_file(file_path, line_num, text, files_dict, file):
    """Function that reads individual file and looks for magic
    text within file.  If it finds it, logs line number and file
    name where found."""
    current_line = 1
    with open(file_path) as f:
        for line in f:
            if current_line >= line_num:
                if text in line:
                    logger.info(
                        'Magic text found in file {0} at line number {1}'
                        .format(file, current_line))
            current_line += 1
    files_dict[file] = current_line
    return files_dict


def watch_directory(files_dict, watch_dir, file_ext, search_text):
    """This function gets ran baised on polling interval.  It builds
    list of current files and passes them along to add and delete
    detections, then calls read files to search for magic text"""
    try:
        only_files = [f for f in listdir(watch_dir)
                      if isfile(join(watch_dir, f))]
    except OSError as err:
        logger.error(err)
    else:
        try:
            files_dict = detect_added_files(files_dict, only_files, file_ext)
            logger.debug(files_dict)
            files_dict = detect_removed_files(files_dict, only_files)
        except Exception as e:
            logger.exception(e)
        for k, v in files_dict.items():
            try:
                filename, file_extension = splitext(k)
            except Exception as e:
                logger.error(e)
            else:
                file = join(watch_dir, k)
                if file_extension == file_ext:
                    try:
                        files_dict = read_file(
                            file, v, search_text, files_dict, k)
                    except Exception as e:
                        logger.exception(e)
    finally:
        return files_dict


def create_parser():
    """Parser to add command line arugments required to run program"""
    parser = argparse.ArgumentParser(
        description="Watches a directory for files that contain search text"
    )
    parser.add_argument(
        '-p', '--pollint', help="Interval which it scans directory",
        type=int, default=1)
    parser.add_argument(
        'searchText', help="Text that will be searched for")
    parser.add_argument(
        '-fe', '--fileExt', help="Extension of files to search")
    parser.add_argument('watchDir', help="Directory to watch")
    return parser


def calculate_run_time(start_time, end_time):
    """Function that takes in start and end epoch time
    and calculates time between the two.  Returns
    string of days, hours, minutes, seconds"""
    total_time = end_time - start_time
    days = total_time // 86400
    hours = total_time // 3600 % 24
    minutes = total_time // 60 % 60
    seconds = total_time % 60
    result = '{0} days, {1} hours, {2} minutes and {3} seconds'.format(
        days, hours, minutes, seconds
    )
    return result


def main(args):
    """Main function used to initialize program and start
    watch_directory"""
    global exit_flag
    # log app start time
    start_time = time.time()
    logger.info('{0} dirwatcher.py started {1}'.
                format(banner_text, banner_text))

    # create a defualt dictonary to store file list
    files_dict = defaultdict(list)

    # creates parser for program
    try:
        parser = create_parser()
        ns = parser.parse_args(args)
    except Exception as e:
        logger.exception(e)
    # captures signals from OS
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # verifies name space was created
    if not ns:
        logger.exception('Arguments not passed correctly')
        parser.print_help()

    # sets local variables to passed in args
    polling_interval = ns.pollint
    magic_text = ns.searchText
    file_ext = ns.fileExt
    watch_dir = ns.watchDir

    # main loop that continues to watch dir
    while not exit_flag:
        try:
            files_dict = watch_directory(
                files_dict, watch_dir, file_ext, magic_text)
        except Exception as e:
            logger.exception(e)
            exit_flag = True
        finally:
            time.sleep(polling_interval)
    end_time = time.time()
    run_time = calculate_run_time(start_time, end_time)

    logger.info('{0} dirwatcher.py stopped \n running time {1}{2}'
                .format(banner_text, run_time, banner_text))


if __name__ == '__main__':
    main(sys.argv[1:])
