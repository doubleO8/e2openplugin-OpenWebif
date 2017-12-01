#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import pprint

from enigma import eDVBDB
from Components.NimManager import nimmanager
import Components.ParentalControl

SLM_MODE_BOTH = "0"
SLM_MODE_LAMEDB = "1"
SLM_MODE_BOUQUET = "2"
SLM_MODE_TRANSPONDERS = "3"
SLM_MODE_PARENTALCONTROL = "4"


class ServiceListsManager(object):
    """
    Controller for reloading service lists, transponders,
    parental control black-/white lists and lamedb.
    """

    def __init__(self):
        self.log = logging.getLogger(__name__)
        self.eDVBDB = eDVBDB.getInstance()
        self.mode_map = {
            SLM_MODE_BOTH: {
                "description": "reloading lamedb and user bouquets",
                "funcs": (self._reload_lamedb, self._reload_user_bouquets)
            },
            SLM_MODE_LAMEDB: {
                "description": "reloading lamedb",
                "funcs": (self._reload_lamedb,)
            },
            SLM_MODE_BOUQUET: {
                "description": "reloading user bouquets",
                "funcs": (self._reload_user_bouquets,)
            },
            SLM_MODE_TRANSPONDERS: {
                "description": "reloading transponders",
                "funcs": (self._reload_transponders,)
            },
            SLM_MODE_PARENTALCONTROL: {
                "description": "reloading parental control white-/blacklists",
                "funcs": (self._reload_parental_control_lists,)
            }
        }

    def _reload_lamedb(self):
        """
        Reload lamedb.

        Returns:
            ?
        """
        self.log.debug("reloading")
        return self.eDVBDB.reloadServicelist()

    def _reload_user_bouquets(self):
        """
        Reload User Bouquets.

        Returns:
            ?
        """
        self.log.debug("reloading")
        return self.eDVBDB.reloadBouquets()

    def _reload_transponders(self):
        """
        Reload Transponders.

        Returns:
            ?
        """
        self.log.debug("reloading")
        return nimmanager.readTransponders()

    def _reload_parental_control_lists(self):
        """
        Reload Parental Control Black/White Lists.

        Returns:
            ?
        """
        self.log.debug("reloading")
        return Components.ParentalControl.parentalControl.open()

    def reload(self, mode=None):
        """
        Reload items based on *mode*.

        Args:
            mode (basestring): Reload mode indicator

        Returns:
            dict: resultset
        """
        result = {
            "result": False
        }

        if mode is not None:
            mode = mode[0]
        self.log.debug("mode={!r}".format(mode))

        try:
            plan = self.mode_map[mode]
            result['message'] = plan['description']
            result['rcs'] = list()
            for func in plan['funcs']:
                rc = func()
                result['rcs'].append(repr(rc))
            result['result'] = True
        except KeyError:
            message_parts = ['missing or wrong parameter mode. Dial ']
            for key in self.mode_map:
                message_parts.append("{!r} for {!s}".format(
                    key, self.mode_map[key]['description']))
            result['message'] = ', '.join(message_parts)
        except Exception as gexc:
            result['message'] = repr(gexc)

        self.log.debug("result:")
        [self.log.debug(line) for line in pprint.pformat(result).split("\n")]

        return result
