import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd
import pickle

tree = ET.parse('veh_od_psrc.rou.xml')
root = tree.getroot()

unique_trips = {}
features = ["type", "depart", "fromTaz", "toTaz"]

for trip in root.findall('./trip'):
    trip_id = trip.get("id")
    trip_data = {feature: trip.get(feature) for feature in features}
    unique_trips[trip_id] = trip_data

depart_hour = {5:0, 6:0, 7:0, 8:0, 9:0, 10:0}
origin = {}
destination = {}
non_pass = 0

for id, info in unique_trips.items():
    if info['type'] != 'passenger':
        non_pass+=1

    hour = float(info['depart'])//3600
    depart_hour[hour] += 1

    o = info['fromTaz']
    if origin.get(o) is None:
        origin[o] = 1
    else:
        origin[o] += 1

    d = info['toTaz']
    if destination.get(d) is None:
        destination[d] = 1
    else:
        destination[d] += 1

print('x')
