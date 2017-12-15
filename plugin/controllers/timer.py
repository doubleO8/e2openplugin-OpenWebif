#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

import enigma
from enigma import eServiceReference

from events import EventsController
from models.timers import TimerDict


class TimersController(object):
    """
    Timers controller
    """

    def __init__(self, *args, **kwargs):
        self.log = logging.getLogger(__name__)
        self.service_center_instance = enigma.eServiceCenter.getInstance()
        self.encoding = kwargs.get("encoding", "utf-8")
        self.rt = kwargs.get("rt")
        # OR MAYBE: ["timer_list", "processed_timers"] ?
        self.sources = kwargs.get("sources", ["timer_list"])
        self.egon = EventsController()

    def _valid_service_reference_or_bust(self, service_reference):
        if not service_reference:
            raise ValueError("invalid service reference: {!r}".format(
                service_reference))
        sr_obj = eServiceReference(service_reference)
        if sr_obj.valid() != 1:
            raise ValueError("invalid service reference: {!r}".format(
                service_reference))
        return sr_obj

    def remove(self, service_reference, item_id):
        # sr_obj = self._valid_service_reference_or_bust(service_reference)
        raise NotImplementedError

    def list_items(self, service_reference=None, item_id=None):
        """
        Generate a list of timers, either **all**,
        **timers for service** or **specific timer of service**.

        Args:
            service_reference (basestring): Service reference string
            item_id (int): Timer ID
        Returns:
            generator: matching :py:obj:`TimerDict` items
        """
        self.log.debug('%s',
                       "Trying to list timer in {!r}".format(self.sources))

        if service_reference:
            sr_obj = self._valid_service_reference_or_bust(service_reference)
            service_reference = sr_obj.toCompareString()

        current_sources = []
        for source in self.sources:
            current_sources += getattr(self.rt, source)

        do_all = service_reference is None and item_id is None
        do_single = service_reference is not None and item_id is not None

        self.log.debug("Listing items ... {!r} / {!r}".format(
            service_reference, item_id))
        self.log.debug("do all={!r} do_single={!r}".format(do_all, do_single))

        for timer_item in current_sources:
            timer_sref, timer_id = str(timer_item.service_ref), timer_item.eit
            e_data = None
            data = TimerDict(timer_item)

            if timer_sref and timer_id:
                e_data = self.egon.lookup_event(timer_sref, timer_id)

            if e_data:
                data['event'] = e_data

            if do_all:
                yield data
            elif do_single:
                if timer_sref == service_reference and timer_id == item_id:
                    self.log.debug("service_reference + item_id")
                    yield data
                    break
            elif service_reference and timer_sref == service_reference:
                self.log.debug("service_reference")
                yield data
