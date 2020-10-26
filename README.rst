.. This README is meant for consumption by humans and pypi. Pypi can render rst files so please do not use Sphinx features.
   If you want to learn more about writing documentation, please check out: http://docs.plone.org/about/documentation_styleguide.html
   This text does not appear on pypi or github. It is a comment.

.. image::
   https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336
       :target: https://pycqa.github.io/isort/

===============================
visaplan.plone.staticthumbnails
===============================

This Plone add-on adds "static" thumbnails to content objects; the idea is

- to make thumbnail images available even for objects the user can't access
  (e.g. for object listings which include restricted but offered objects)

- since the Zope permissions system is bypassed anyway, the front-end webserver
  can quite as well serve those images itself;

- thus, the thumbnails are written to the filesystem.


Features
--------

- Provides a mixin class `IStaticThumbnails`
- which features the `getThumbnailPath` method.
- This method checks the date and time of the image in the ``image`` property
  and creates any missing thumbnail image in the filesystem
- before returning the TTW path to this image file,
- which usually follows the pattern `/++thumbnail++/<UUID>`.
- It is not normally executed during the common web requests but only when
  the object is reindexed; thus, the TTW path to the thumbnail image is
  available as catalog metadata.


Examples
--------

This add-on can be seen in action at the following sites:

- https://www.unitracc.de
- https://www.unitracc.com


Documentation
-------------

Sorry, we don't have real user documentation yet.


Installation
------------

Install visaplan.plone.staticthumbnails by adding it to your buildout::

    [buildout]

    ...

    eggs =
        visaplan.plone.staticthumbnails


and then running ``bin/buildout``


Contribute
----------

- Issue Tracker: https://github.com/visaplan/plone.staticthumbnails/issues
- Source Code: https://github.com/visaplan/plone.staticthumbnails


Support
-------

If you are having issues, please let us know;
please use the `issue tracker`_ mentioned above.


License
-------

The project is licensed under the GPLv2.

.. _`issue tracker`: https://github.com/visaplan/plone.staticthumbnails/issues

.. vim: tw=79 cc=+1 sw=4 sts=4 si et
