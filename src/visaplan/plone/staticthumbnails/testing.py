# -*- coding: utf-8 -*-
# Python compatibility:
from __future__ import absolute_import

# Standard library:
import warnings

with warnings.catch_warnings():
    warnings.simplefilter('ignore', ImportWarning)

    # from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
    from plone.app.testing import applyProfile
    from plone.app.testing import FunctionalTesting
    from plone.app.testing import IntegrationTesting
    from plone.app.testing import PLONE_FIXTURE
    from plone.app.testing import PloneSandboxLayer
    from plone.testing import z2

# visaplan:
import visaplan.plone.staticthumbnails


class VisaplanPloneStaticthumbnailsLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load any other ZCML that is required for your tests.
        # The z3c.autoinclude feature is disabled in the Plone fixture base
        # layer.
        # Plone:
        import plone.app.dexterity
        self.loadZCML(package=plone.app.dexterity)
        self.loadZCML(package=visaplan.plone.staticthumbnails)

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'visaplan.plone.staticthumbnails:default')


VISAPLAN_PLONE_STATICTHUMBNAILS_FIXTURE = VisaplanPloneStaticthumbnailsLayer()


VISAPLAN_PLONE_STATICTHUMBNAILS_INTEGRATION_TESTING = IntegrationTesting(
    bases=(VISAPLAN_PLONE_STATICTHUMBNAILS_FIXTURE,),
    name='VisaplanPloneStaticthumbnailsLayer:IntegrationTesting',
)


VISAPLAN_PLONE_STATICTHUMBNAILS_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(VISAPLAN_PLONE_STATICTHUMBNAILS_FIXTURE,),
    name='VisaplanPloneStaticthumbnailsLayer:FunctionalTesting',
)


# VISAPLAN_PLONE_STATICTHUMBNAILS_ACCEPTANCE_TESTING = FunctionalTesting(
#     bases=(
#         VISAPLAN_PLONE_STATICTHUMBNAILS_FIXTURE,
#         REMOTE_LIBRARY_BUNDLE_FIXTURE,
#         z2.ZSERVER_FIXTURE,
#     ),
#     name='VisaplanPloneStaticthumbnailsLayer:AcceptanceTesting',
# )
