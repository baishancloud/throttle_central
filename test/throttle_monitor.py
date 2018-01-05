import json
import sys
sys.path.append('/usr/local/s2/current')

import clusterinforeader
import websocketutil


def request_one_ip(ip, port, body_str):
    with websocketutil.throttle_wrapper(ip) as cli:
        cli.send(body_str)
        data = cli.recv()

    return data


def ws_request(body, **argkv):
    if 'ips' in argkv:
        ips = argkv['ips']
    else:
        ips = clusterinforeader.ips_by_roleidc(['ThrottleCentral'], None)

    port = argkv.get('port', 7070)

    for ip in ips:
        try:
            body_str = json.dumps(body)
            resp_data = request_one_ip(ip, port, body_str)
            result = json.loads(resp_data)
            return result
        except Exception:
            if ip == ips[-1]:
                raise


# subject:
#     connections
#     reported
#     consumption_sum
#     rejection_sum
#     distribution
#     quota


def monitor(subject, **argkv):
    body = {
        'monitor': subject,
    }

    if argkv.get('start_slot') is not None:
        body['start_slot'] = argkv['start_slot']

    if argkv.get('end_slot') is not None:
        body['end_slot'] = argkv['end_slot']

    result = ws_request(body, **argkv)
    return result


if __name__ == '__main__':
    print monitor('consumption_sum')
