import unittest, sys, inspect
from django.conf import settings
from django.utils.importlib import import_module
from molly.core.handlers import BaseView
from molly.core.breadcrumbs import NullBreadcrumb
from search import GoogleSearch

class Argspec(tuple):
    args = property(lambda self: self[0])
    varargs = property(lambda self: self[1])
    keywords = property(lambda self: self[2])
    defaults = property(lambda self: self[3])

def getargspec(*args, **kwargs):
    return Argspec(inspect.getargspec(*args, **kwargs))

class GenericSearchTestCase(unittest.TestCase):
    def testViewSignatures(self):
        for app_name in settings.INSTALLED_APPS:
            try:
                views = import_module(app_name+'.views')
            except ImportError:
                continue

            for view_name in dir(views):

                view = getattr(views, view_name)

                if not isinstance(view, type):
                    continue

                if not BaseView in view.__mro__:
                    continue

                metadata_sig = None
                breadcrumb_sig = None
                handler_sigs = []
                initial_context_sig = None

                for func_name in dir(view):
                    func = getattr(view, func_name)
                    
                    
                    if func_name == 'get_metadata':
                        metadata_sig = getargspec(func)
                    elif func_name == 'initial_context':
                        initial_context_sig = getargspec(func)
                    elif func_name.startswith('handle_') and func_name[7:].upper() == func_name[7:]:
                        handler_sigs.append( (func_name, getargspec(func)) )
                    elif func_name == 'breadcrumb':
                        if func is NullBreadcrumb:
                            breadcrumb_sig = True
                            continue
                        else:
                            breadcrumb_sig = getargspec(func.breadcrumb_func)
                    else:
                        continue
                    
                    if func_name in view.__dict__:
                        self.assert_(
                            isinstance(view.__dict__[func_name], classmethod),
                            "%s.%s.%s must be a classmethod, not %s" % (
                                app_name, view_name, func_name, type(view.__dict__[func_name])
                            )
                        )

                if not handler_sigs:
                    continue
                    
                if not breadcrumb_sig:
                    self.fail('%s.%s does not define a breadcrumb' % (app_name, view_name))

                # Keep track of the first handler sig to compare things to
                fhn, fhs = handler_sigs[0]
                
                self.assertEqual(
                    fhs.args[:3],
                    ['cls','request','context'],
                    "View handler %s.views.%s.%s must take (cls, request, context) as its first three arguments" % (
                        app_name, view_name, fhn,
                    )
                )

                for handler_name, argspec in handler_sigs:
                    self.assertEqual(
                        fhs, argspec,
                        'View handler signatures differ for %s.views.%s: %s and %s' % (
                            app_name, view_name, fhn, handler_name
                        ),
                    )
                    self.assertEqual(
                        argspec.varargs, None,
                        "View handler %s.views.%s.%s takes *%s when it shouldn't" % (
                            app_name, view_name, handler_name, argspec.varargs
                        ),
                    )
                    self.assertEqual(
                        argspec.keywords, None,
                        "View handler %s.views.%s.%s takes **%s when it shouldn't" % (
                            app_name, view_name, handler_name, argspec.keywords
                        ),
                    )

                if not (initial_context_sig.varargs or initial_context_sig.keywords):
                    self.assertEqual(
                        initial_context_sig.args,
                        fhs.args[:2] + fhs.args[3:],
                        "initial_context for %s.views.%s has a signature inconsistent with the handlers" % (
                            app_name, view_name,
                        )
                    )

                if metadata_sig:
                    self.assertEqual(
                        metadata_sig.args,
                        fhs.args[:2] + fhs.args[3:],
                        "get_metadata for %s.views.%s has a signature inconsistent with the handlers" % (
                            app_name, view_name,
                        )
                    )
                    self.assertEqual(
                        metadata_sig.varargs, None,
                        "get_metadata() for %s.views.%s takes *%s when it shouldn't" % (
                            app_name, view_name, metadata_sig.varargs
                        ),
                    )
                    self.assertEqual(
                        metadata_sig.keywords, None,
                        "get_metadata() for %s.views.%s takes **%s when it shouldn't" % (
                            app_name, view_name, metadata_sig.keywords
                        ),
                    )
                
                if breadcrumb_sig != True:
                    self.assertEqual(
                        breadcrumb_sig, fhs,
                        "breadcrumb signature for %s.%s differs from its view handlers (%s, %s)" % (
                            app_name, view_name, breadcrumb_sig, fhs
                        )
                    )


