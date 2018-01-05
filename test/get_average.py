import sys
import time

sys.path.append('/usr/local/s2/current')

from pykit import utfjson
from pykit import dictutil


consumption = []
rejection = []

f = open('loop_monitor_report.txt', 'r')

while True:
    line = f.readline()
    if line == '':
        break

    parts = utfjson.load(line.strip())

    consumption.append(parts[1] or {})
    rejection.append(parts[2] or {})

nr_slot = len(consumption)
print 'total slot: %d' % nr_slot

total_consumption = {}
total_rejection = {}

for i in range(len(consumption)):
    dictutil.addto(total_consumption, consumption[i])
    dictutil.addto(total_rejection, rejection[i])

print'total_consumption:'
print total_consumption

print 'total rejection:'
print total_rejection

for k, v in total_consumption.iteritems():
    total_consumption[k] = float(v) / nr_slot

print 'average:'
print total_consumption
