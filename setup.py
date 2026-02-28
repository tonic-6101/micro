# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic

from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

with open("VERSION") as f:
	version = f.read().strip()

setup(
	name="micro",
	version=version,
	description="Business organizer for micro businesses",
	author="Tonic",
	author_email="tonic@example.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires,
	license="AGPL-3.0",
)
