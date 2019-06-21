# -*- coding: utf-8 -*-
# Standardmodule
from urlparse import urlunsplit
from urllib import urlencode
from os import getcwd
from os.path import normpath, join, abspath
from StringIO import StringIO
from collections import defaultdict

from Products.CMFCore.utils import getToolByName


from PIL.Image import (Image, open as open_image,
        # "Resampling-Filter":
        ANTIALIAS, LINEAR, CUBIC,
        BILINEAR,  # Empfehlung von RL
        )

# Unitracc-Tools:
from visaplan.kitchen.spoons import extract_1st_image_info
from visaplan.tools.debug import pp, log_or_trace
from visaplan.tools.files import make_mtime_checker
from visaplan.plone.tools.context import message
from visaplan.plone.tools.log import getLogSupport
from visaplan.tools.minifuncs import gimme_False
logger, debug_active, DEBUG = getLogSupport()

logger.warning('TODO: find a clean way to detect the var/ directory')
try:
    from Products.unitracc.tools.info import VAR_ROOT
except ImportError:
    from os.path import dirname, pardir, join, normpath
    from sys import executable
    logger.warning('Using sys.executable %(executable)r', locals())
    VAR_ROOT = join(dirname(executable), pardir, 'var')
logger.info('Using VAR_ROOT %(VAR_ROOT)r', locals())

try:
    import subprocess32 as subprocess
except ImportError:
    logger.warning("Can't import subprocess32")
    import subprocess
call = subprocess.call

get_mtime = make_mtime_checker(makemissingdirs=True,
                               logger=logger)
lot_kwargs = {'logger': logger,
              'debug_level': debug_active or 0,
              'trace': 1,
              }

# interfaces are not yet really used:
from .interfaces import (IDedicatedThumbnail, IThumbnailFromText,
	IThumbnailFromFirstImage, IThumbnailFromPage,
	)

# ----------------------------- [ Katalog-Metadaten: getThumbnailPath ... [
class ThumbnailMixin:  # ------------------------------------------ [[
    """
    Mixin-Klasse für Objekte, die in Suchergebnislisten mit einem
    Vorschaubild dargestellt werden - sei es ein dediziertes
    (UnitraccNews), das erste im Text verwendete (UnitraccNews,
    UnitraccArtiole), die Nutzlast selbst (UnitraccImage) oder ein vom
    Medientyp nahegelegtes (Videos, Animationen).

    Achtung:
    - Etwa benötigte Datenfelder (image, text ...) werden von dieser
      Mixin-Klasse (noch?) *nicht* erledigt!
    """
    # --------------------------------------------- [ Daten ... [
    # Wenn geändert, müssen ggf. die Metadaten "getThumbnailPath" neu
    # erzeugt werden; um Vorschaubilder neu zu erzeugen, ohne daß sich die
    # Basis-Bilder geändert haben, die entsprechenden Vorschaubilder löschen
    # (oder mit dem touch-Tool ein sehr altes Änderungsdatum setzen)
    THUMBNAIL_SCALING = '240x180'

    # Verarbeitung durch vorgeschalteten Server:
    THUMBNAIL_PREFIX = '/++thumbnail++/'

    # Die ID eines Feldes im AT-Schema, das für die Vorschau verwendet werden
    # soll:
    THUMBNAIL_FIELDID = None  # überschrieben in DedicatedThumbnailMixin
    # --------------------------------------------- ] ... Daten ]

    def _getThumbnailPhysicalPath(self, uid):
        """
        Gib den für das Vorschaubild zu verwendenden Pfad im Dateisystem zurück
        """
        rel = join(VAR_ROOT, 'thumbnails', uid)
        return rel

    @log_or_trace(**lot_kwargs)
    def _getPathOfNewOrExistingThumbnail(self, uid):
        """
        Wenn das Vorschaubild noch aktuell ist, gib den Pfad zurück;
        wenn nicht, erzeuge es vorher.
        """
        img_id = self.THUMBNAIL_FIELDID
        o = None
        if img_id:
            filename = self._getThumbnailPhysicalPath(uid)
            imgfield = self.getField(img_id)
            if imgfield:  # hat scale-Methode
                o = imgfield.getRaw(self)
        if o is None:  # kein image-Feld vorhanden
            return None  # pep 20.2

        str_o = str(o)
        if not str_o:  # vorhandenes image-Feld ist leer
            # Das ist bei UnitraccNews-Objekten durchaus häufig:
            logger.info('%(self)r.getThumbnailPath: Bilddaten sind leer', locals())
            return None  # pep 20.2

        # o = self.getThumbnailImageObject()
        # auf den Wahrheitswert von o ist leider kein Verlaß!
        try:
            prefix = self.THUMBNAIL_PREFIX
            if not prefix:
                raise ValueError('Kein Praefix fuer Vorschaubild-Pfade!'
                                 ' (%(self)r, %(uid)r, prefix=%(prefix)r)'
                                 % locals())

            force = defaultdict(gimme_False)
            try:
                form = o.REQUEST.form
                form_force = form.get('force', {})
                # Checkbox erzeugt ggf. den Wert 'on' (oder nichts); siehe (gf):
                # ../browser/unitraccsearch/templates/brain_maintenance_view.pt
                force.update(form_force)
            except Exception as e:
                logger.error('Error evaluating the force arguments!'
                             ' (proceeding anyway)')
                logger.exception(e)

            scale_to_size = map(int, self.THUMBNAIL_SCALING.split('x'))
            fs_mtime = get_mtime(filename)
            if fs_mtime is None:
                logger.info('%(self)r.getThumbnailPath: no image %(filename)r yet', locals())
            # TODO: Lock auf Datei <filename>
            else:
                log_thumbnail(filename)
                logger.info('mtime: %s (%s)', fs_mtime, filename)
                logger.info('mtime: %s (%r data)', o._p_mtime, imgfield)
                if o._p_mtime <= fs_mtime:
                    if o._p_mtime is None:
                        logger.warn('%(self)r.getThumbnailPath:'
                                    ' image object has no modification date/time (ZODB)',
                                    locals())
                    else:
                        logger.info('%(self)r.getThumbnailPath: %(img_id)r not changed', locals())
                        if force['replace-thumbnail']:
                            logger.info('%(self)r.getThumbnailPath: recreating anyway!', locals())
                        else:
                            return prefix+uid
                else:
                    logger.info('%(self)r.getThumbnailPath: %(img_id)r has changed', locals())
            virtualfile = StringIO(str_o)
            try:
                img = open_image(virtualfile)
                target_width, target_height = scale_to_size
                # aktuell hartcodierte Skalierungslogik:
                # - falls zu breit, maßstäblich verkleinern
                # - falls dann noch zu hoch, unten abschneiden
                # TODO: Wählbare Strategien ...
                #  - oben oder links
                #  - unten oder rechts
                #  - horizontal oder vertikal zentriert
                #  - nicht beschneiden, sondern skalieren und ggf. auffüllen

                if o.width > target_width:
                    fact = target_width * 1.0 / o.width
                    new_height = int(o.height * fact)
                    if new_height:
                        # auch hier kann noch ein IOError auftreten!
                        img = img.resize((target_width, new_height),
                                         resample=BILINEAR)
                    current_width, current_height = img.size
                    logger.info('%(self)r.getThumbnailPath:'
                                ' scaled image by factor %(fact)0.2f'
                                ' to WxH=%(current_width)rx%(current_height)r',
                                locals())
                else:
                    current_width, current_height = o.width, o.height
                    logger.info('%(self)r.getThumbnailPath:'
                                ' matches target width %(target_width)r, current'
                                ' WxH=%(current_width)rx%(current_height)r',
                                locals())
                if current_height > target_height:
                    img = img.crop((0, 0, current_width, target_height))
                    logger.info('%(self)r.getThumbnailPath:'
                                ' cropped image to target height, '
                                ' WxH=%(current_width)rx%(target_height)r',
                                locals())
                elif current_height < target_height:
                    logger.warning('%(self)r.getThumbnailPath:'
                                ' insufficient height, '
                                ' WxH=%(current_width)rx%(current_height)r',
                                locals())
                mimetype = imgfield.getContentType(self)
                subtype = mimetype.split('/')[1]
            except IOError as e:
                logger.error('%(self)r.getThumbnailPath: %(e)r', locals())
            else:
                try:
                    img.save(filename, subtype)
                    img.close()
                except IOError as e:
                    logger.error('%(self)r.getThumbnailPath:'
                                 "error %(e)r while saving to '%(filename)s'",
                                 locals())
                except Exception as e:
                    logger.error('%(self)r.getThumbnailPath (uid=%(uid)r) :'
                                 'PIL complains, %(e)r',
                                 locals())
                else:
                    logger.info('%(self)r.getThumbnailPath:'
                                " saved thumbnail image to '%(filename)s'",
                                locals())
                    return prefix+uid
                finally:
                    log_thumbnail(filename)
        except AttributeError as e:
            logger.error('%(e)r', locals())
            logger.exception(e)
            logger.info('ist ok, oder?')
        except ValueError:
            raise

    @log_or_trace(**lot_kwargs)
    def getThumbnailPath(self, done_uids=None):
        """
        Für Metadaten: gib den Pfad zur Thumbnail-Datei zurück

        Die Methoden der Schleife werden von den abgeleiteten Klassen
        (DedicatedThumbnailMixin, ThumbnailFromTextMixin ...)
        bereitgestellt, die per "Duck-Typing" erkannt werden.

        Um Probleme beim Zugriff auf Vorschaubilder nicht-öffentlicher Objekte
        zu vermeiden, werden diese fertig skaliert im Dateisystem abgelegt, wo
        sie vom Apache-Browser ausgeliefert werden können.

        Dies hat als willkommenen Nebeneffekt große Performanz-Vorteile:
        - Es werden die Python-Threads nicht belastet
        - Apache kann so etwas vermutlich ohnehin schneller als Plone

        Wenn das Vorschaubild keine (wie auch immer geartete) Eigenschaft des
        Objekts ist, sondern vom Typ abhängt, ist es üblicherweise nicht über
        eine UID zugänglich; in diesen Fällen wird weiterhin der bisherige
        Bildpfad verwendet (z. B. von _buildStaticThumbnailPath erzeugt), der
        ebenfalls auf eine Dateisystem-Ressorce verweisen kann.
        """
        o = None
        uid = self._getUID()

        # weiterzureichen für rekursiven Aufruf:
        if done_uids is None:
            done_uids = set([uid])
        else:
            if uid in done_uids:
                return None
            done_uids.add(uid)

        val = self._getPathOfNewOrExistingThumbnail(uid)  # --> IDedicatedThumbnail
        if val:
            return val
        # TODO: Vorschaubild im Dateisystem loeschen, sofern vorhanden

        portal_catalog = None
        for name in ('_getImageDictFromTextFields',    # --> IThumbnailFromText
                     '_getThumbnailPathOfFirstImage',  # --> IThumbnailFromFirstImage
                     '_getImageDictFromStandardPage',  # --> IThumbnailFromPage
                     ):
            if 0 and name == '_getImageDictFromTextFields':
                from pdb import set_trace; set_trace()
            method = getattr(self, name, None)
            if method is not None:
                dic = method()
                if dic is None:
                    continue
                if isinstance(dic, basestring):
                    return dic
                if dic:
                    assert dic.keys() == ['uid']
                    if portal_catalog is None:
                        portal_catalog = getToolByName(self, 'portal_catalog')
                    brains = portal_catalog({'UID': dic['uid']})
                    number = len(brains)
                    if number != 1:
                        logger.info('dic=%(dic)r --> %(number)d hits', locals())
                    for brain in brains:
                        o2 = brain.getObject()
                        if o2:
                            val = o2.getThumbnailPath(done_uids)
                            if val:
                                return val

        return self._getDefaultThumbnailPath()

    def hasImage(self):  # (derzeit auch ein eigenständiges Metadatenfeld)
        """
        Enthält das Schema dieses Typs ein spezielles Bild, das für
        Übersichten verwendet werden soll - und ist dieses auch gefüllt?
        """
        img_id = self.THUMBNAIL_FIELDID
        if not img_id:
            return False
        return self._hasImage(img_id)

    def _hasImage(self, name):
        imgfield = self.getField(name)
        if imgfield:
            imgsize = imgfield.get_size(self)
            if imgsize:
                return True

    def getThumbnailResponse(self):
        """
        Zur Verwendung als Antwort auf /thumbnail_image/<uid>
        bzw. context.getBrowser('thumbnail').get_for_uid(<uid>)

        Wird nur benötigt für DedicatedThumbnailMixin;
        für ThumbnailFromTextMixin wird die UID des textuell verknüpften Bildes
        verwendet und damit *dessen* getThumbnailResponse-Methode aufgerufen.
        """
        o = self.getThumbnailImageObject()
        response = self.REQUEST.RESPONSE
        setHeader = response.setHeader
        if o:
            # TODO: Zwischenspeicherung des skalierten Bildes
            pass

    def getThumbnailImageObject(self):  # --> IDedicatedThumbnail
        """
        Hilfsmethode für --> getThumbnailResponse:
        gib das *eigene* Bild-Feld zurück, das für die Vorschau skaliert werden
        soll, oder None
        """
        img_id = self.THUMBNAIL_FIELDID
        if not img_id:
            return None  # pep 20.2
        imgfield = self.getField(img_id)
        if imgfield:
            return imgfield.getRaw(self)
        return None  # pep 20.2

    def _getDefaultThumbnailPath(self):
        """
        Die letzte Möglichkeit: das Standardpiktogramm, oder None
        """
        return None

    def _buildStaticThumbnailPath(self, name, scaling):
        """
        Wie --> _buildStaticImagePath, aber mit scaling-Komponente

        Aufgerufen von überschriebenen Versionen von _getDefaultThumbnailPath
        """
        # z. B. /news_default_180x180.jpg
        return ('/++resource++unitracc-images/%(name)s_default_%(scaling)s.jpg'
                % locals())

    def _buildStaticImagePath(self, name):
        """
        Aufgerufen von überschriebenen Versionen von _getDefaultThumbnailPath
        """
        # z. B. /code/picto_courseview.jpg
        return ('/++resource++unitracc-images/%(name)s'
                % locals())
    # ----------------------------------------- ] ... ThumbnailMixin ]


class DedicatedThumbnailMixin(ThumbnailMixin):  # ----------------- [[
    """
    Objekte, die ein spezielles Bildfeld haben, das für das
    Vorschaubild verwendet werden soll.

    Kann kombiniert werden mit --> ThumbnailFromTextMixin.
    """

    THUMBNAIL_FIELDID = 'image'

    def _getPrimaryImagePath(self):  # obsolet? --> _getPrimaryImageData
        """
        Aufgerufen durch getThumbnailPath()

        Version von UnitraccNews; funktioniert jedoch vermutlich auch
        für alle anderen Datentypen mit image-Feld.  Ansonsten:

        raise NotImplemented
        """
        if self.hasImage():
            return urlunsplit(['', '',  # ohne Protokoll und Hostnamen
                               '/@@news/getImage',
                               urlencode([('scaling', self.THUMBNAIL_SCALING),
                                          ('uid', self._getUID()),
                                          ]),
                               ''])

    def _getPrimaryImageData(self, name='image'):  # obsolet?
        """
        Aufgerufen durch getThumbnailPath()
        """
        imgfield = self.getField(name)
        if imgfield:
            imgsize = len(imgfield.image)
            response = self.REQUEST.RESPONSE
            setHeader = response.setHeader

    # -------------------------------- ] ... DedicatedThumbnailMixin ]


class ThumbnailFromTextMixin(ThumbnailMixin):  # ------------------ [[
    """
    Objekte, für die das Vorschaubild aus dem Text ermittelt werden soll
    (wenn kombiniert mit --> DedicatedThumbnailMixin: nur, wenn kein
    dediziertes Vorschaubild ermittelt werden konnte).
    """

    def _getImageDictFromTextFields(self):
        """
        Extrahiere den ersten Verweis zu einem verwendeten Bild aus dem
        (untransformierten) HTML-Text

        Aufgerufen durch getThumbnailPath(); siehe ./base.py
        """
        text = self.getRawText()
        if text:
            return extract_1st_image_info(text)
    # --------------------------------- ] ... ThumbnailFromTextMixin ]


class ThumbnailFromFirstImageMixin(ThumbnailMixin):  # ------------ [[
    """
    Ordnerartige Objekte können Bildobjekte enthalten;
    das "erste" wird als Vorschaubild verwendet.
    """

    def _getThumbnailPathOfFirstImage(self):
        """
        Verwende das erste Bild, das direkt im vorliegenden Ordner abgelegt ist;
        rufe ggf. direkt dessen getThumbnailPath-Methode auf.
        """
        # Wenn der Ordner Bilder enthält, nimm das erste:
        query = {'portal_type': ['UnitraccImage',
                                 ],
                 'getExcludeFromNav': False,
                 'sort_on': 'getObjPositionInParent',
                 'path': {'query': self.getPath(),
                          'depth': 1},
                 'Language': 'all',
                 }
        catalog = getToolByName(self, 'portal_catalog')
        brains = catalog(query)
        for brain in brains:
            o = brain.getObject()
            if o is not None:
                return o.getThumbnailPath()
    # ----------------------------] ... ThumbnailFromFirstImageMixin ]


class ThumbnailFromPageMixin(ThumbnailMixin):  # ------------------ [[
    """
    Objekte, für die das Vorschaubild aus dem Text *einer aufgeschalteten
    Seite* ermittelt werden soll: wie ThumbnailFromTextMixin,
    aber für Ordner, die üblicherweise keinen eigenen hierfür zu verwendenden
    Text haben.
    """
    def _getImageDictFromStandardPage(self):
        """
        Extrahiere den ersten Verweis zu einem verwendeten Bild aus dem
        (untransformierten) HTML-Text der Standardseite

        Aufgerufen durch getThumbnailPath(); siehe ./base.py
        """
        layout = self.getLayout()
        if layout in ('default_page_view',
                      'document_view',
                      'folder_listing',
                      ):
            # wenn eine Standardseite aufgeschaltet ist und der Text dieser Seite
            # Bilder enthält, verwende das erste Bild.
            # Achtung - diese Ermittung des Ansichtsdokuments
            #           ist noch nicht über alle Zweifel erhaben!
            page = self.getBrowser('subportal').get_default_page()
            # ATDocument hat keine Methode getThumbnailPath;
            # eine solche ist auch absichtlich noch undefiniert
            # (sie könnte zukünftig einen Mini-Screenshot erzeugen und
            # bereitstellen). Vorerst wird das erste angesprochene Bild
            # verwendet.
            if page:
                text = page.getRawText()
                if text:
                    return extract_1st_image_info(text)
    # --------------------------------- ] ... ThumbnailFromPageMixin ]


class VoidThumbnailMixin(ThumbnailMixin):  # ---------------------- [[
    """
    Objekte, für die es (noch) keine sinnvollen Vorschaubilder gibt
    """

    def getThumbnailPath(self):
        """
        Es gibt kein sinnvolles Vorschaubild
        """
        return None  # pep 20.2
    # ------------------------------------- ] ... VoidThumbnailMixin ]
# ----------------------------- ] ... Katalog-Metadaten: getThumbnailPath ]
# vim: ts=8 sts=4 sw=4 si et hls
