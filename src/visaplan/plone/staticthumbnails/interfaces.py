# -*- coding: utf-8 -*-
"""Module where all interfaces, events and exceptions live."""

# Python compatibility:
from __future__ import absolute_import

# Zope:
from zope.interface import Interface
from zope.publisher.interfaces.browser import IDefaultBrowserLayer


class IVisaplanPloneStaticthumbnailsLayer(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""

# ------------------------------- [ options for getThumbnailPath ... [
class IThumbnail(Interface):
    """ Support static thumbnails somehow
    """

class IDedicatedThumbnail(IThumbnail):
    """ Take thumbnail from the image attribute
    """

class IThumbnailFromText(IThumbnail):
    """ Take thumbnail from the first mentioned image in text
    """

class IThumbnailFromFirstImage(IThumbnail):
    """ Take thumbnail from the first image here (for folders)
    """

class IThumbnailFromPage(IThumbnail):
    """ Take thumbnail from the configured default page
    """

class IVoidThumbnail(IThumbnail):
    """ There is no meaningful thumbnail
    """
# ------------------------------- ] ... options for getThumbnailPath ]
