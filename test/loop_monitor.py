import sys
import time
sys.path.append('/usr/local/s2/current')

import throttle_monitor
from pykit import timeutil
from pykit import utfjson


def get_user_quota(quota, user_name):
    user_quota = {}
    for node_id, node_quota in quota.iteritems():
        front_quota = node_quota['front']

        for slot, slot_quota in front_quota.iteritems():
            v = slot_quota.get(user_name)
            if v is not None:
                user_quota[node_id] = v

    return user_quota


def one_loop(curr_slot, user_name):
    start_slot = curr_slot - 4
    consumption_sum_resp = throttle_monitor.monitor(
        'consumption_sum', start_slot=start_slot, end_slot=curr_slot)

    if str(start_slot) not in consumption_sum_resp:
        print 'slot %d not in consumption_sum resp' % start_slot
        return

    rejection_sum_resp = throttle_monitor.monitor(
        'rejection_sum', start_slot=start_slot, end_slot=curr_slot)

    if str(start_slot) not in rejection_sum_resp:
        print 'slot %d not in rejection_sum resp' % start_slot
        return

    quota_resp = throttle_monitor.monitor(
        'quota', start_slot=start_slot, end_slot=curr_slot)

    if str(start_slot) not in quota_resp:
        print 'slot %d not in quota resp' % start_slot
        return

    user_consumption_sum = consumption_sum_resp[
        str(start_slot)]['front'].get(user_name)

    user_rejection_sum = rejection_sum_resp[
        str(start_slot)]['front'].get(user_name)

    quota = quota_resp[str(start_slot)]

    user_quota = get_user_quota(quota, user_name)

    time_str = timeutil.format_ts(start_slot, 'mysql')
    print time_str
    print '%s\n%s\n%s\n' % (repr(user_consumption_sum),
			    repr(user_rejection_sum),
			    repr(user_quota))

    line = utfjson.dump([time_str,
                         user_consumption_sum,
                         user_rejection_sum,
                         user_quota])
    with open('loop_monitor_report.txt', 'a') as f:
        f.write(line + '\n')


def loop_monitor(user_name):
    count = 0
    while True:
        curr_slot = int(round(time.time()))
        one_loop(curr_slot, user_name)
        count += 1
        if count >= 300:
            break

        to_sleep = curr_slot + 1 - time.time()
        if to_sleep < 0:
            to_sleep = 0.01

        time.sleep(to_sleep)


if __name__ == '__main__':
    loop_monitor('throttle_test')
