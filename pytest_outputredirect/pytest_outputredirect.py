##
# @file pytest-outputredirect.py
# @author Sam Lea (samjl) <samjlea@gmail.com>
# @created 25/07/17
# @brief pytest output redirect - Adds output redirection functionality
# to loglevels plugin.
# Requires: pytest-loglevels
# Issues: 1. does not support terminal markup applied by pytest,
#         2. pytest output that fills console width stretches to 2
#            lines after the addition on log level etc.

import ConfigParser
import json
import os
import pkg_resources
import pytest
import re
import sys
from collections import OrderedDict


class DebugFunctionality:
    def __init__(self, name, enabled):
        self.name = name
        self.enabled = enabled

DEBUG = {"output-redirect": DebugFunctionality("redirect", True)}


def pytest_addoption(parser):
    # Add disable redirection command line option.
    parser.addoption("--no-redirect", action="store_true",
                     help="Disable output redirection (disables plugin). "
                          "Overrides value set in config.cfg")
    parser.addoption('--root-dir', type=str, default=None,
                     help='Full path to local base directory to save test '
                          'logs to. Overrides value set in config.cfg')
    parser.addoption("--no-json", action="store_true",
                     help="Don't save log to JSON file (std out only)")


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    # Load user defined configuration from file
    config_path = pkg_resources.resource_filename('pytest_outputredirect', '')
    parser = ConfigParser.ConfigParser()
    parser.read(os.path.join(config_path, "config.cfg"))

    for functionality in DEBUG.keys():
        try:
            DEBUG[functionality].enabled = parser.getboolean("debug",
                                                             functionality)
        except Exception as e:
            print e

    if config.getoption("--no-json"):
        LogOutputRedirection.json_log = False
        _debug_print("JSON logging is disabled (command line)",
                     DEBUG["output-redirect"])
    else:
        LogOutputRedirection.json_log = not(parser.getboolean("general",
                                                              "no-json"))
        _debug_print("JSON logging is {}abled (config.cfg)"
                     .format("en" if LogOutputRedirection.json_log else "dis"),
                     DEBUG["output-redirect"])

    if not (config.getoption("--no-redirect") or
            isinstance(sys.stdout, LogOutputRedirection)):
        log_redirect = LogOutputRedirection()
        sys.stderr = log_redirect
        sys.stdout = log_redirect

    if LogOutputRedirection.json_log:
        root_dir = config.getoption("--root-dir")
        if not root_dir:
            root_dir = parser.get("general", "root-dir")
            _debug_print("Using root directory {} (config.cfg)"
                         .format(root_dir), DEBUG["output-redirect"])
        else:
            _debug_print("Using root directory '{}' (command line)"
                         .format(root_dir), DEBUG["output-redirect"])
        LogOutputRedirection.root_directory = root_dir
        # Create root logs directory if required
        if not os.path.exists(LogOutputRedirection.root_directory):
            _debug_print("Creating directories {}".format(LogOutputRedirection.
                                                          root_directory),
                         DEBUG["output-redirect"])
            os.makedirs(LogOutputRedirection.root_directory)

        open(os.path.join(LogOutputRedirection.root_directory, "session.json"),
             'w').close()
        LogOutputRedirection.session_file_path = os.path.join(
            LogOutputRedirection.root_directory, "session.json")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_setup(item):
    _debug_print("Creating log file for module {}, test function {}".format(
        item.module.__name__, item.name), DEBUG["output-redirect"])

    if LogOutputRedirection.json_log:
        # Create module dir if required and test function dir within
        # this and then module_function.json file
        path_to_test_dir = os.path.join(LogOutputRedirection.root_directory,
                                        item.module.__name__, item.name)
        _debug_print("Path to test directory: {}".format(path_to_test_dir),
                     DEBUG["output-redirect"])
        if not os.path.exists(path_to_test_dir):
            _debug_print("Creating directories", DEBUG["output-redirect"])
            os.makedirs(path_to_test_dir)

        open(os.path.join(path_to_test_dir, "log.json"), 'w').close()
        LogOutputRedirection.test_file_path = os.path.join(path_to_test_dir,
                                                           "log.json")
        _debug_print("Path to json log file: {}".format(
            LogOutputRedirection.test_file_path), DEBUG["output-redirect"])

    yield


@pytest.hookimpl(hookwrapper=True)
def pytest_report_teststatus(report):
    yield
    if report.when == "teardown":
        _debug_print("OUTPUTREDIRECT LAST TEARDOWN MESSAGE",
                     DEBUG["output-redirect"])
        LogOutputRedirection.test_file_path = None


def _is_start_or_end(msg):
    # Detect the start/beginning or end of pytest test section.
    search = re.search("(={6}).*(begin|start|end|passed|failed|skipped)|"
                       "(-{6}).*(begin|start).*", msg.lower())
    return True if search is not None else False


class LogOutputRedirection:
    # Output redirection class. Redirects sys.stdout and stderr to
    # write method below.
    messageIndex = 0
    json_log = None
    # json log file paths
    root_directory = None
    session_file_path = None  # created at plugin configuration stage
    test_file_path = None  # file is created in setup phase

    def __init__(self):
        self.printStdout = sys.stdout
        self.printStderr = sys.stderr

    def write(self, msg):
        if not pytest.redirect.is_level_set():
            msg_list = msg.split('\n')
            msg_list = filter(None, msg_list)
            for msg_line in msg_list:
                level_reset_required = _is_start_or_end(msg)
                if level_reset_required:
                    log_level = pytest.redirect.set_level(1)
                else:
                    log_level = pytest.redirect.increment_level(1)
                step, index = pytest.redirect.get_step_for_level(log_level)
                self.write_log_step(msg_line, log_level, step, index)
                pytest.redirect.increment_level(-1)

        else:
            log_level = pytest.redirect.get_current_level()
            step, index = pytest.redirect.get_current_step(log_level)
            if msg == "":
                # Printing empty message
                self.write_log_step(msg, log_level, step, index)
            else:
                # split \n and print separately for each line
                msg_list = msg.split('\n')
                msg_list = filter(None, msg_list)
                if msg_list:
                    self.write_log_step(msg_list[0], log_level, step, index)
                    if len(msg_list) > 1:
                        for msg_line in msg_list[1:]:
                            # If the message has been split into multiple
                            # lines then for each line the step and index
                            # are incremented. A possible design change
                            # could be to increment the index but keep
                            # the step the same. Would also apply to if
                            # log level is not set condition above.
                            step, index = pytest.redirect.get_step_for_level(log_level)
                            self.write_log_step(msg_line, log_level, step,
                                                index)

    def flush(self):
        # Do nothing. Flush is performed in write -> write_log_step ->
        # writeToStdout
        return

    def isatty(self):
        return False

    def write_log_step(self, msg, level, step, index):
        # Write the log message to all enabled outputs.
        msg = re.sub('[\r\n]', '', msg)
        msg = msg.rstrip()

        if not isinstance(msg, unicode):
            msg = unicode(msg, errors='replace')

        log_entry = OrderedDict()
        log_entry["index"] = index
        log_entry["level"] = level
        log_entry["step"] = step
        log_entry["text"] = msg

        self.printStdout.write("{0[level]}-{0[step]} [{0[index]}] {0[text]}\n"
                               .format(log_entry))
        self.printStdout.flush()

        # Complete session json log file.
        # Ensure the file always contains valid JSON.
        if LogOutputRedirection.json_log and \
                LogOutputRedirection.session_file_path:
            if os.stat(LogOutputRedirection.session_file_path).st_size != 0:
                with open(LogOutputRedirection.session_file_path, "rb+") as f:
                    f.seek(-2, os.SEEK_END)
                    f.write(",\n")
            with open(LogOutputRedirection.session_file_path, "a") as f:
                if os.stat(LogOutputRedirection.session_file_path).st_size == 0:
                    f.write("[")
                json.dump(log_entry, f, separators=(",", ":"))
                f.write("]\n")

        # Test function specific json log file. Contains setup, call
        # and teardown.
        if LogOutputRedirection.json_log and \
                LogOutputRedirection.test_file_path:
            if os.stat(LogOutputRedirection.test_file_path).st_size != 0:
                with open(LogOutputRedirection.test_file_path, "rb+") as f:
                    f.seek(-2, os.SEEK_END)
                    f.write(",\n")
            with open(LogOutputRedirection.test_file_path, "a") as f:
                if os.stat(LogOutputRedirection.test_file_path).st_size == 0:
                    f.write("[")
                json.dump(log_entry, f, separators=(",", ":"))
                f.write("]\n")


def _debug_print(msg, flag):
    # Print a debug message if the corresponding flag is set.
    if flag.enabled:
        print "DEBUG({}): {}".format(flag.name, msg)
