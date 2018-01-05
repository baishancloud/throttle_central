import sys
import time

sys.path.append('/usr/local/s2/current')

from pykit import utfjson
from pykit import dictutil


consumption = []
rejection = []

f = open('loop_monitor_report.txt', 'r')

total = 0
reject = 0
all_reject = 0

while True:
    line = f.readline()
    if line == '':
        break

    total += 1
    parts = utfjson.load(line.strip())

    if parts[2] is not None:
        reject += 1

        if parts[1] is None:
            all_reject += 1


print 'total: %d' % total
print 'reject: %d' % reject
print 'all reject: %d' % all_reject
print 'part reject: %d' % (reject - all_reject)
