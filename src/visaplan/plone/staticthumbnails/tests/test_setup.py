# -*- coding: utf-8 -*-
"""Setup tests for this package."""
# Python compatibility:
from __future__ import absolute_import

# Standard library:
import unittest

# Plone:
from plone import api
from plone.app.testing import TEST_USER_ID, setRoles

# visaplan:
from visaplan.plone.staticthumbnails.testing import \
    VISAPLAN_PLONE_STATICTHUMBNAILS_INTEGRATION_TESTING  # noqa


class TestSetup(unittest.TestCase):
    """Test that visaplan.plone.staticthumbnails is properly installed."""

    layer = VISAPLAN_PLONE_STATICTHUMBNAILS_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')

    def test_product_installed(self):
        """Test if visaplan.plone.staticthumbnails is installed."""
        self.assertTrue(self.installer.isProductInstalled(
            'visaplan.plone.staticthumbnails'))

    def test_browserlayer(self):
        """Test that IVisaplanPloneStaticthumbnailsLayer is registered."""
        # Plone:
        from plone.browserlayer import utils

        # visaplan:
        from visaplan.plone.staticthumbnails.interfaces import (
            IVisaplanPloneStaticthumbnailsLayer,
            )
        self.assertIn(
            IVisaplanPloneStaticthumbnailsLayer,
            utils.registered_layers())


class TestUninstall(unittest.TestCase):

    layer = VISAPLAN_PLONE_STATICTHUMBNAILS_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')
        roles_before = api.user.get_roles(TEST_USER_ID)
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.installer.uninstallProducts(['visaplan.plone.staticthumbnails'])
        setRoles(self.portal, TEST_USER_ID, roles_before)

    def test_product_uninstalled(self):
        """Test if visaplan.plone.staticthumbnails is cleanly uninstalled."""
        self.assertFalse(self.installer.isProductInstalled(
            'visaplan.plone.staticthumbnails'))

    def test_browserlayer_removed(self):
        """Test that IVisaplanPloneStaticthumbnailsLayer is removed."""
        # Plone:
        from plone.browserlayer import utils

        # visaplan:
        from visaplan.plone.staticthumbnails.interfaces import (
            IVisaplanPloneStaticthumbnailsLayer,
            )
        self.assertNotIn(
            IVisaplanPloneStaticthumbnailsLayer,
            utils.registered_layers())
