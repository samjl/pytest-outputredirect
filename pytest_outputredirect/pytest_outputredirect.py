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

import pytest
import re
import sys
from collections import OrderedDict


def pytest_addoption(parser):
    # Add disable redirection command line option.
    parser.addoption("--no-redirect", action="store_true",
                     help="Disable output redirection (disables plugin)")


def pytest_configure(config):
    # Process plugin command line arguments. Enable/disable redirection.
    if not (config.getoption("--no-redirect") or
            isinstance(sys.stdout, LogOutputRedirection)):
        log_redirect = LogOutputRedirection()
        sys.stderr = log_redirect
        sys.stdout = log_redirect


def _is_start_or_end(msg):
    # Detect the start/beginning or end of pytest test section.
    search = re.search("(={6}).*(begin|start|end|passed|failed|skipped)|"
                       "(-{6}).*(begin|start).*", msg.lower())
    return True if search is not None else False


class LogOutputRedirection:
    # Output redirection class. Redirects sys.stdout and stderr to
    # write method below.
    messageIndex = 0

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
