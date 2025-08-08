from flask import Blueprint


def create_blueprint(name):
    """Create a blueprint with the given name"""
    return Blueprint(name, __name__)
