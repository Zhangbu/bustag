#!/usr/bin/env python
"""
Backward compatibility entry point for setup.py.

This file exists for compatibility with tools that don't support pyproject.toml.
All configuration is now in pyproject.toml.
"""
from setuptools import setup

if __name__ == "__main__":
    setup()