import os
import sys
import pytest

from sam.app import App

def test_settings_initialized():
    app = App('foo', debug=True)
    assert(type(app.settings) == dict)
