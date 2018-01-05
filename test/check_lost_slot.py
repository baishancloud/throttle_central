import sys
import time
sys.path.append('/usr/local/s2/current')

from pykit import timeutil
from pykit import utfjson

f = open('loop_monitor_report.txt', 'r')

i = 0
last_ts = None

while True:
    line = f.readline()
    if line == '':
        break

    parts = utfjson.load(line.strip())
    r = timeutil.parse(parts[0], 'mysql')
    ts = time.mktime(r.timetuple())

    if last_ts is None:
        i += 1
        last_ts = ts
        continue

    if ts != last_ts + 1:
        print '%d line: %s not adjacent to last line' % (i, line)
        break

    i += 1
    last_ts = ts


print 'no lost slot'
