<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
#   Table of Content

- [Name](#name)
- [Status](#status)
- [Description](#description)
- [Install](#install)
- [Usage](#usage)
- [Update sub repo](#update-sub-repo)
- [Methods](#methods)
  - [throttle_central.manager.run](#throttle_centralmanagerrun)
    - [prototype](#prototype)
    - [arguments](#arguments)
- [Author](#author)
- [Copyright and License](#copyright-and-license)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

#   Name

throttle_central:
A python lib used to set resource quota for each node.

#   Status

This library is in beta phase.

It has been used heavily in our object storage service, as a foundamental
library of our devops platform.

#   Description

This lib must be used with [lua-resty-throttle](https://github.com/baishancloud/lua-resty-throttle).
The main purpose of this module is to find out how many resources
each user have consumed on all nodes in every seconds, check if someone
used too much, find out how many a user can use in next few seconds, also
distribute the amount of resource usable by a user among all nodes.

#   Install

This package does not support installation.

Just clone it and copy it into your project source folder.

```
cd your_project_folder
git clone https://github.com/baishancloud/throttle_central.git
```

#   Usage

```python
from throttle_central import manager

class ThrottleCentralLock(Object):
    def __enter__(self):
        print 'try to get lock'

    def __exit__(self, type, value, traceback):
        print 'release lock'

def list_limits(service_name):
    return [
        {
            # 'username' and 'limit' are mandatory
            'username': 'test_user',
            'limit': {
                'traffic_down': 1024,
                'database_read': 1024,
                'database_write': 1024,
                'traffic_up': 10240,
             },
            'ts': '1513681047768',
            'service': 'front',
        },
    ]


argkv = {
    'ip': '127.0.0.1',
    'port': 7075,
    'nr_slot': 60,
    'Lock': ThrottleCentralLock,
    'list_limits': list_limits,
}

manager.run(**argkv)
```

#  Update sub repo

>   You do not need to read this chapter if you are not a maintainer.

First update sub repo config file `.gitsubrepo`
and run `git-subrepo`.

`git-subrepo` will fetch new changes from all sub repos and merge them into
current branch `mater`:

```
./script/git-subrepo/git-subrepo
```

`git-subrepo` is a tool in shell script.
It merges sub git repo into the parent git working dir with `git-submerge`.

#   Methods

##  throttle_central.manager.run

Start the service

### prototype

```python
throttle_central.manager.run(**argkv)
```

### arguments

It receive the following arguments:

- `argkv` is a dict contains some optional arguments.
    It can contains the following arguments:

    - `ip` the ip address to listen on for receiving info reported
         by node module.

    - `port` the socket port to use.

    - `nr_slot` set how many slots to keep, default is 60.

    - `Lock` a lock class that can be used in a 'with' statement,
        for high reliability, we need to set up several central node,
        but only the node which got lock will actually do work.

    - `list_limits` a callback function used to get all limit settings
        for a service, the prototype is: `list_limits(service_name)`

#   Author

Renzhi (任稚) <zhi.ren@baishancloud.com>

#   Copyright and License

The MIT License (MIT)

Copyright (c) 2016 Renzhi (任稚) <zhi.ren@baishancloud.com>
