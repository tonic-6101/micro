# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic

import frappe
from frappe.model.document import Document


class MicroSettings(Document):
	def validate(self):
		self.detect_orga_integration()
		self.ensure_disclaimer()
		self.validate_capacity_hours()

	def validate_capacity_hours(self):
		"""Clamp monthly capacity hours to 40–200 range."""
		if self.monthly_capacity_hours:
			if self.monthly_capacity_hours < 40:
				self.monthly_capacity_hours = 40
			elif self.monthly_capacity_hours > 200:
				self.monthly_capacity_hours = 200

	def detect_orga_integration(self):
		"""Auto-detect if Orga app is installed."""
		installed_apps = frappe.get_installed_apps()
		if "orga" in installed_apps:
			self.enable_orga_integration = 1

	def ensure_disclaimer(self):
		"""G4: Ensure disclaimer is set based on language."""
		if not self.draft_disclaimer:
			from micro.services.compliance import get_disclaimer_text

			self.draft_disclaimer = get_disclaimer_text(self.default_language)
