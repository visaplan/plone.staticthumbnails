# -*- coding: utf-8 -*-
"""Module where all interfaces, events and exceptions live."""

from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope.interface import Interface


class IVisaplanPloneStaticthumbnailsLayer(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""

# ------------------------------- [ options for getThumbnailPath ... [
class IDedicatedThumbnail(Interface):
    """ Take thumbnail from the image attribute
    """

class IThumbnailFromText(Interface):
    """ Take thumbnail from the first mentioned image in text
    """

class IThumbnailFromFirstImage(Interface):
    """ Take thumbnail from the first image here (for folders)
    """

class IThumbnailFromPage(Interface):
    """ Take thumbnail from the configured default page
    """

class IVoidThumbnail(Interface):
    """ There is no meaningful thumbnail
    """
# ------------------------------- ] ... options for getThumbnailPath ]
