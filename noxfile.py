import os

import nox
from nox import options

PATH_TO_PROJECT = os.path.join(".")

options.sessions = ["format_fix"]


@nox.session()
def format_fix(session: nox.Session):
    session.install("black")
    session.install("isort")
    session.run("python", "-m", "black", PATH_TO_PROJECT)
    session.run("python", "-m", "isort", PATH_TO_PROJECT)
