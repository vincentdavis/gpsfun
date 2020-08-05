#!/usr/bin/env python

"""Rally Style Tests"""

import pytest
# import unittest
# from pathlib import Path
from datetime import datetime
from datetime import timedelta
from gpsfun.readers import tcx, gpx, gpsbabel
from gpsfun.tracks import Track
from gpsfun.rallystyle import RallyResults

@pytest.fixture
def roubaix():
    return [{'Segment_name':'Ride Start: lap 1',
            'location': {'lat': 40.117348, 'lon': -105.258836},
            'type_name': 'transport',
            'type_args': {'timed': None}
            },
          {'Segment_name':'End lap 1, Refuel, ride to start',
            'location': {'lat': 40.116263, 'lon': -105.257817},
            'type_name': 'transport',
            'type_args': {'timed': None},
            },
           {'Segment_name':'Race: Lap two',
            'location': {'lat': 40.117348, 'lon': -105.258836},
            'type_name': 'timed',
            'type_args': None,
           },
             {'Segment_name':'Finish',
            'location': {'lat': 40.116263, 'lon': -105.257817},
            'type': 'end'
             }
           ]

def test_roubaix_1(roubaix):
    rfile = "test_data/rallystyle/roubaix/dan_b.gpx"
    rs = RallyResults(df=Track(gpsbabel(str(rfile))).df, segments=roubaix)
    rs.match_checkpoints()
    rs.calc_results()
    assert rs.results[0]['duration'] == timedelta(hours=1, minutes=2, seconds=2)
    assert rs.results[0]['total_timed'] == timedelta(0)
    assert rs.results[1]['duration'] == timedelta(hours=0, minutes=0, seconds=33)
    assert rs.results[1]['total_timed'] == timedelta(0)
    assert rs.results[2]['duration'] == timedelta(hours=0, minutes=50, seconds=12)
    assert rs.results[2]['total_timed'] == timedelta(hours=0, minutes=50, seconds=12)
    assert rs.results[-1]['total_timed'] == timedelta(days=0, minutes=50, seconds=12)
    assert rs.results[-1]['duration'] == None


def test_roubaix_2(roubaix):
    rfile = "test_data/rallystyle/roubaix/dean_d.fit"
    rs = RallyResults(df=Track(gpsbabel(str(rfile))).df, segments=roubaix)
    rs.match_checkpoints()
    rs.calc_results()
    # todo finish

def test_roubaix_3(roubaix):
    rfile = "test_data/rallystyle/roubaix/jennifer_g.gpx"
    rs = RallyResults(df=Track(gpsbabel(str(rfile))).df, segments=roubaix)
    rs.match_checkpoints()
    rs.calc_results()
    # todo finish


def test_roubaix_4(roubaix):
    rfile = "test_data/rallystyle/roubaix/michelle_m.gpx"
    rs = RallyResults(df=Track(gpsbabel(str(rfile))).df, segments=roubaix)
    rs.match_checkpoints()
    rs.calc_results()
    # todo finish


def test_roubaix_5(roubaix):
    rfile = "test_data/rallystyle/roubaix/richard_e.gpx"
    rs = RallyResults(df=Track(gpsbabel(str(rfile))).df, segments=roubaix)
    rs.match_checkpoints()
    rs.calc_results()
    assert rs.results[-1]['Segment_name'] == 'Finish'
    assert rs.results[-1]['location'] == {'lat': 40.116263, 'lon': -105.257817}
    assert rs.results[-1]['type'] == 'end'
    assert rs.results[-1]['duration'] == None
    assert rs.results[-1]['total_timed'] == timedelta(hours=1, minutes=8, seconds=53)
