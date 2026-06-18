import os

from kivy.metrics import dp, sp


def handle_dp(value):
    """Avoid EventLoop.ensure_window() when run on GitHub runner"""
    if "GITHUB_ACTIONS" in os.environ:
        return value
    else:
        return dp(value)


def handle_sp(value):
    """Avoid EventLoop.ensure_window() when run on GitHub runner"""
    if "GITHUB_ACTIONS" in os.environ:
        return value
    else:
        return sp(value)
