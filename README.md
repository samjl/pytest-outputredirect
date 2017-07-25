# pytest-outputredirect Plugin

Expands upon and requires pytest-loglevels (installed automatically by this 
plugin).

Redirects all stdout and stderr to the plugin so a log level and step can be
 applied to the message before output. In addition to the loglevels plugin 
 an overall message index (or counter) is added.
  
## Install

Download and build the [pytest-loglevels](https://github.com/samjl/pytest-loglevels) and pytest-outputredirect packages:

    python setup.py bdist_wheel
(wheel python plugin is required for build step)

Copy dist/pytest_loglevels-... .whl to a local python plugin server

    pip install pytest-outputredirect
    
## loglevels API usage
See pytest-loglevels [documentation](https://github.com/samjl/pytest-loglevels)

## Test Implementation
From console run pytest using the -s (--capture=no).

Example test code:

    from py.test import log
    
    
    def test_logging():
        print "Hello world"    
        log.high_level_step("Woo Hoo!")
        log.detail_step("It works 1!")
        log.detail_step("It works 2!")
        log.step("It still works 3!")
        log.step("This line contains a line break here\nand then continues!")
        print "Has this been incremented?"
        print "Is this the same level as last msg?"
        print "This is a regular print statement with a line break here\nwith this text on the next line"
        log.step("It still works 4!")
        log.detail_step("It works 5!")
        print "Goodbye"

In the output below the format is:

log_level-step_for_level [message_index] message

    1-1 [1] ======================================================================================================== test session starts =========================================================================================================
    2-1 [2] platform linux2 -- Python 2.7.6, pytest-2.9.2, py-1.4.34, pluggy-0.3.1
    2-2 [3] rootdir: /home/slea1/workspace/pytest_plugins/plugin_testing, inifile:
    2-3 [4] plugins: outputredirect-0.1.0, loglevels-0.2.0
    2-4 [5] collected 1 items
    2-5 [6] test_logging_line_break.py
    2-6 [7] Hello world
    1-2 [8] Woo Hoo!
    2-1 [9] It works 1!
    2-2 [10] It works 2!
    2-3 [11] It still works 3!
    2-4 [12] This line contains a line break here
    2-5 [13] and then continues!
    3-1 [14] Has this been incremented?
    3-2 [15] Is this the same level as last msg?
    3-3 [16] This is a regular print statement with a line break here
    3-4 [17] with this text on the next line
    2-6 [18] It still works 4!
    2-7 [19] It works 5!
    3-1 [20] Goodbye
    3-2 [21] .
    1-3 [22] ====================================================================================================== 1 passed in 0.00 seconds ======================================================================================================
    