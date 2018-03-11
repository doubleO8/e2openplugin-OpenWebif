#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. seealso::

    http://mslowik.blogspot.de/


.. _event_format-label:

Possible Values of the Format Field
+++++++++++++++++++++++++++++++++++

+------+----------------------------------------------------------------------+
|VALUE | DESCRIPTION                                                          |
+======+======================================================================+
| I    | Event Id                                                             |
+------+----------------------------------------------------------------------+
| B    | Event Begin Time                                                     |
+------+----------------------------------------------------------------------+
| D    | Event Duration                                                       |
+------+----------------------------------------------------------------------+
| T    | Event Title                                                          |
+------+----------------------------------------------------------------------+
| S    | Event Short Description                                              |
+------+----------------------------------------------------------------------+
| E    | Event Extended Description (extended event description)              |
+------+----------------------------------------------------------------------+
| C    | Current Time                                                         |
+------+----------------------------------------------------------------------+
| R    | Service Reference                                                    |
+------+----------------------------------------------------------------------+
| N    | Service Name                                                         |
+------+----------------------------------------------------------------------+
| n    | Short Service Name                                                   |
+------+----------------------------------------------------------------------+
| X    | A flag not associated with the returned result indicating that the   |
|      | minimum of one item in the result table is to be returned            |
|      | corresponding to each service, even if no service events are found.  |
|      | In cases where no event is found in the resulting rows of the table, |
|      | undefined values are returned as None                                |
+------+----------------------------------------------------------------------+

Event Search
============


Method signature::

    search((fmt, int size, int querytype, int PE1, int PE2))

Description of Search Parameters
++++++++++++++++++++++++++++++++

+-----------+----------+------------------------------------------------------+
| PARAMETER | REQUIRED | DESCRIPTION                                          |
+===========+==========+======================================================+
| fmt       | required | Returned data format - see :ref:`event_format-label` |
+-----------+----------+------------------------------------------------------+
| size      | required | maximum number of returned rows                      |
+-----------+----------+------------------------------------------------------+
| querytype | required | query type                                           |
+-----------+----------+------------------------------------------------------+
| PE1       | required | Parameters dependent on the context set by           |
|           |          | querytype                                            |
+-----------+----------+ see :ref:`event_search_parameters-label`             +
| PE2       | optional |                                                      |
|           |          |                                                      |
+-----------+----------+------------------------------------------------------+


.. _event_search_parameters-label:

Description of Parameters Related to Search Querytype
+++++++++++++++++++++++++++++++++++++++++++++++++++++

+------+--------------------------------+-------------------+-----------------+
| TYPE | DESCRIPTION                    | PE1               | PE2             |
+======+================================+===================+=================+
| 0    | Find similar events            | service reference | Event ID        |
|      | (SIMILAR_BROADCASTINGS_SEARCH) |                   |                 |
+------+--------------------------------+-------------------+-----------------+
| 1    | Find events with the exact     | text to search    | 0 = CASE_CHECK  |
|      | title (EXAKT_TITLE_SEARCH)     |                   | 1 = NO_CASECHECK|
+------+--------------------------------+-------------------+-----------------+
| 2    | Find events with text in the   | text to search    | 0 = CASE_CHECK  |
|      | title (PARTIAL_TITLE_SEARCH)   |                   | 1 = NO_CASECHECK|
+------+--------------------------------+-------------------+-----------------+

.. note::

    * This function searches for event information for the specified \
    parameters.
    * The information is returned in the form of a two-dimensional array, \
    where the first dimension defines the individual elements of the cursor \
    (the searched events), and the second dimension is the value \
    corresponding to the event that is specified by the Format field \
    (single event data).

Example (https://mslowik.blogspot.de)::

  l = eEPGCache.getInstance().search(
     ('RIBND', 1024, eEPGCache.SIMILAR_BROADCASTINGS_SEARCH, refstr, event_id))



Event Lookup
============


Method signature::

    lookupEvent([fmt,
                (eServiceReference ref, int querytype, int PE1, int PE2)])


Description of Lookup Parameters
++++++++++++++++++++++++++++++++

+-----------+----------+------------------------------------------------------+
| PARAMETER | REQUIRED | DESCRIPTION                                          |
+===========+==========+======================================================+
| fmt       | required | Returned data format - see :ref:`event_format-label` |
+-----------+----------+------------------------------------------------------+
| ref       | required | reference to service                                 |
+-----------+----------+------------------------------------------------------+
| querytype | required | query type                                           |
+-----------+----------+------------------------------------------------------+
| PE1       | required | Parameters dependent on the context set by           |
|           |          | querytype.                                           |
+-----------+----------+ see :ref:`event_lookup_parameters-label`             |
| PE2       | optional |                                                      |
|           |          |                                                      |
+-----------+----------+------------------------------------------------------+


.. _event_lookup_parameters-label:

Description of Parameters Related to Querytype
++++++++++++++++++++++++++++++++++++++++++++++

+-------+--------------------------------------------+--------------+---------+
| TYPE  | DESCRIPTION                                | PE1          | PE2     |
+=======+============================================+==============+=========+
|  2    | Request an event ID                        | Event ID     | n/a     |
+-------+--------------------------------------------+--------------+---------+
| -1    | request events *before* the specified time | time horizon | end     |
+-------+--------------------------------------------+              + date of +
|  0    | request events *crossing* specified time   |              | search  |
+-------+--------------------------------------------+              + scope   +
| +1    | request events *after* specified time      |              |         |
+-------+--------------------------------------------+--------------+---------+

.. note::

    * **-1** for *time horizon* is current date.
    * This function searches for event information for the specified \
    parameters.
    * The information is returned in the form of a two-dimensional array, \
    where the first dimension defines the individual elements of the cursor \
    (the searched events), and the second dimension is the value \
    corresponding to the event that is specified by the Format field \
    (single event data).
    * Time zones of type NUMBER are defined as the number of seconds since \
    the EPOCH date (in the unix systems beginning in 1970).

.. note::

    * for *querytype=2, (PE2) minutes=0* PE1 is event ID
    * PE2 appers to be search scope timedelta in *minutes*
    * if timedelta in *minutes* is -1 all matching events are returned(?)
    * for *querytype=3*: last known item(?)

Examples (https://mslowik.blogspot.de)::

    events = eEPGCache.getInstance ().lookupEvent(
        ['IBDTSENC', (ref, 0, begintime, endtime)])

    search = ['IBDCTSERNX']
    if services: # It's a Bouquet
        search.extend ([(service, 0, -1) cho service in services])
    events = eEPGCache.getInstance ().lookupEvent (search)

    search = ['IBDCTSERNX']
    if services: # It's a Bouquet
        search.extend ([(service, 0, -1) cho service in services])
    events = eEPGCache.getInstance().lookupEvent(search)

    event = eEPGCache.getInstance().lookupEvent(['ESX', (ref, 2, int (idev))]

"""
import logging

from enigma import eEPGCache

from models.events import EventDict, FLAGS_ALL

CASE_SENSITIVE = 0
CASE_INSENSITIVE = 1

QUERYTYPE_SEARCH__SIMILAR_BROADCASTINGS = 0

QUERYTYPE_SEARCH__EXACT_TITLE = 1
QUERYTYPE_SEARCH__PARTIAL_TITLE = 2
QUERYTYPE_SEARCH__SHORT_DESCRIPTION = 3
QUERYTYPE_SEARCH__TITLE_SHORT_DESCRIPTION = 4
QUERYTYPE_SEARCH__EXTENDED_DESCRIPTION = 5
QUERYTYPE_SEARCH__FULL_DESCRIPTION = 6

QUERYTYPE_LOOKUP__BEFORE = -1
QUERYTYPE_LOOKUP__WHILE = 0
QUERYTYPE_LOOKUP__AFTER = 1
QUERYTYPE_LOOKUP__ID = 2

QUERY_TIMESTAMP_CURRENT_TIME = -1
QUERY_MINUTES_ANY = -1


class EventsController(object):
    """
    Events controller.
    """

    def __init__(self, *args, **kwargs):
        self.log = logging.getLogger(__name__)
        self.epgcache_instance = eEPGCache.getInstance()
        self.raise_exceptions = kwargs.get("may_raise", False)
        self.fallback_flags = kwargs.get("fallback_flags", FLAGS_ALL)

    def search(self, what, querytype=None, case_sensitive=False, flags=None,
               max_rows=None):
        """
        Search EPG events

        Args:
            what (basestring): query value
            querytype (int): see :ref:`event_search_parameters-label`
            case_sensitive (bool): True if case sensitive search
            flags(basestring): query flags
            max_rows (int): maximum number of results

        Returns:
            list of matching items
        """
        mangled = []
        case = CASE_INSENSITIVE

        if flags is None:
            flags = self.fallback_flags

        if case_sensitive:
            case = CASE_SENSITIVE

        if querytype is None:
            querytype = QUERYTYPE_SEARCH__PARTIAL_TITLE

        if max_rows is None:
            max_rows = 64

        arglist = (flags, max_rows, querytype, what, case)

        try:
            results = self.epgcache_instance.search(arglist)
            if not results:
                results = []
            for data in results:
                mangled.append(EventDict(data, flag_string=flags))
        except Exception as exc:
            self.log.error(exc)
            if self.raise_exceptions:
                raise

        return mangled

    def lookup(self, service_reference, querytype=None, begin=None,
               minutes=None, flags=None, max_rows=None):
        """
        Lookup EPG events

        Args:
            service_reference (basestring): service reference
            querytype (int): see :ref:`event_lookup_parameters-label`
            begin (int): begin timestamp
            minutes (int): query's time range in minutes
            flags(basestring): query flags
            max_rows (int): maximum number of results

        Returns:
            list: matching items
        """
        mangled = []

        if flags is None:
            flags = self.fallback_flags

        if querytype is None:
            querytype = QUERYTYPE_SEARCH__PARTIAL_TITLE

        if begin is None:
            begin = QUERY_TIMESTAMP_CURRENT_TIME

        if minutes is None:
            minutes = QUERY_MINUTES_ANY

        if querytype == QUERYTYPE_LOOKUP__ID:
            arglist = (service_reference, querytype, begin)
        else:
            arglist = (service_reference, querytype, begin, minutes)

        try:
            results = self.epgcache_instance.lookupEvent([flags, arglist])

            if not results:
                results = []
            if max_rows:
                results = results[:max_rows]
            for data in results:
                mangled.append(EventDict(data, flag_string=flags))
        except Exception as exc:
            self.log.error(exc)
            if self.raise_exceptions:
                raise

        return mangled

    def lookup_event(self, service_reference, event_id, flags=None):
        """
        Lookup EPG event by ID

        Args:
            service_reference (basestring): service reference
            event_id (int): Event ID
            flags(basestring): query flags

        Returns:
            models.events.EventDict: matching item or None
        """
        result = self.lookup(service_reference,
                             querytype=QUERYTYPE_LOOKUP__ID, begin=event_id,
                             flags=flags)
        if result:
            return result[0]
        return None
