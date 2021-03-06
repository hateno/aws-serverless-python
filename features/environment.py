# -- FILE: features/environment.py
from behave import use_fixture
from features.fixtures import *

# USE: behave -D DEBUG         (to enable  debug-on-error)
# USE: behave -D DEBUG=yes     (to enable  debug-on-error)
# USE: behave -D DEBUG=no      (to disable debug-on-error)
DEBUG = False

def setup_debug_on_error(userdata):
    global DEBUG
    DEBUG = userdata.getbool("DEBUG")

def before_all(context):
    setup_debug_on_error(context.config.userdata)

def after_step(context, step):
    if DEBUG and step.status == "failed":
        # -- ENTER DEBUGGER: Zoom in on failure location.
        # NOTE: Use IPython debugger, same for pdb (basic python debugger).
        import ipdb
        ipdb.post_mortem(step.exc_traceback)

def before_tag(context, tag):
    if tag == 'fixture.app':
        use_fixture(app, context)
    if tag == 'fixture.scaffold':
        use_fixture(scaffold, context)
    if tag == 'fixture.logging':
        use_fixture(setlog, context)
