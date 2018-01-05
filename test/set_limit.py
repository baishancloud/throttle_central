import sys
sys.path.append('/usr/local/s2/current')

import throttle_util

limit = {
    'traffic_up': 1024 * 1024 * 100,
    'traffic_down': 1024 * 1024 * 2,
    'database_read': 1024 * 5,
    'database_write': 1024 * 5,
}
#throttle_util.add_limit('front', 'throttle_test', limit)
throttle_util.set_limit('front', 'throttle_test', limit)
throttle_util.get_limit('front', 'throttle_test')
