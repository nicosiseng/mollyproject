# -*- coding: utf-8 -*-

"""Custom Django test runner that runs the tests using the
XMLTestRunner class.

The main reason that made me come up with this project in the first place was
to make it easier to manage the build cycle of my Django applications. Since
I already use Hudson to build my JavaEE applications, it would be nice to
leverage my current setup to handle my Django applications as well.

This script shows how to use the XMLTestRunner in a Django project. To know
how to configure a custom TestRunner in a Django project, please read the
Django docs website.

To fine tune this script, put one or more of the following settings in your
project's 'settings.py' file:

 - TEST_OUTPUT_VERBOSE (default: False)
    Besides the XML reports generated by the test runner, a bunch of useful
    information is printed to the sys.stderr stream, just like the
    TextTestRunner does. Use this setting to choose between a verbose and a
    non-verbose output.

 - TEST_OUTPUT_DESCRIPTIONS (default: False)
    If your test methods contains docstrings, you can display such docstrings
    instead of display the test name (ex: module.TestCase.test_method). In
    order to use this feature, you have to enable verbose output by setting
    TEST_OUTPUT_VERBOSE = True.

 - TEST_OUTPUT_DIR (default:'.')
    Tells the test runner where to put the XML reports. If the directory
    couldn't be found, the test runner will try to create it before
    generate the XML files.
"""

import unittest, xmlrunner

def run_tests(test_labels, verbosity=1, interactive=True,
              extra_tests=(), suite=None):
    """
    Set `TEST_RUNNER` in your settings with this routine in order to
    scaffold test spatial databases correctly for your GeoDjango models.
    For more documentation, please consult the following URL:
      http://geodjango.org/docs/testing.html.
    """
    import os, os.path, shutil
    from django.conf import settings
    from django.db import connection
    from django.db.models import get_app, get_apps
    from django.test.simple import build_suite, build_test, reorder_suite, TestCase
    from django.test.utils import setup_test_environment, teardown_test_environment

    # The `create_test_spatial_db` routine abstracts away all the steps needed
    # to properly construct a spatial database for the backend.
    from django.contrib.gis.db.backend import create_test_spatial_db

    # Setting up for testing.
    setup_test_environment()
    settings.DEBUG = False
    settings.TESTING = True
    old_name = settings.DATABASE_NAME

    settings.CACHE_DIR = os.path.join(os.path.dirname(__file__), 'cache')
    if not os.path.exists(settings.CACHE_DIR):
        os.makedirs(settings.CACHE_DIR)

    settings.FEED_PATH = os.path.join(settings.CACHE_DIR, 'feeds')
    settings.EXTERNAL_IMAGE_DIR = os.path.join(settings.CACHE_DIR, 'external_images')
    settings.GENERATED_MAP_DIR = os.path.join(settings.CACHE_DIR, 'generated_maps')
    settings.OSM_TILE_DIR = os.path.join(settings.CACHE_DIR, 'osm_tiles')

    output = getattr(settings, 'TEST_OUTPUT_FILE', 'test_results.xml')
    output = open(output, 'w')

    # Creating the test spatial database.
    create_test_spatial_db(verbosity=0, autoclobber=not interactive)

    # The suite may be passed in manually, e.g., when we run the GeoDjango test,
    # we want to build it and pass it in due to some customizations.  Otherwise,
    # the normal test suite creation process from `django.test.simple.run_tests`
    # is used to create the test suite.
    if suite is None:
        suite = unittest.TestSuite()
        if test_labels:
            for label in test_labels:
                if '.' in label:
                    suite.addTest(build_test(label))
                else:
                    app = get_app(label)
                    suite.addTest(build_suite(app))
        else:
            for app in get_apps():
                suite.addTest(build_suite(app))

        for test in extra_tests:
            suite.addTest(test)

    suite = reorder_suite(suite, (TestCase,))

    # Executing the tests (including the model tests), and destorying the
    # test database after the tests have completed.

    result = xmlrunner.XMLTestRunner(stream=output).run(suite)

    connection.creation.destroy_test_db(old_name, verbosity=0)
    teardown_test_environment()

    # Remove the cache directories
    shutil.rmtree(settings.CACHE_DIR)

    # Returning the total failures and errors
    return len(result.failures) + len(result.errors)

