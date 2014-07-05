#!/usr/bin/env python
# encoding: utf-8
#
# Copyright © 2014 deanishe@deanishe.net
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
# Created on 2014-07-04
#

"""
Update the cache of git repositories based on the settings in the workflow's
`settings.json` file.
"""

from __future__ import print_function, unicode_literals

import sys
import os
import subprocess
from fnmatch import fnmatch
from time import time
from multiprocessing.dummy import Pool

from workflow import Workflow

# How many search threads to run at the same time
CONCURRENT_SEARCHES = 4

# How deep to search in the directory.
# 1 = look only in specified directory
# 2 = also look in subdirectories of specified directory
DEFAULT_DEPTH = 2

# Will be populated later
log = None
decode = None


def find_git_repos(dirpath, excludes, depth):
    """Return list of directories containing a `.git` directory

    Results matching globbing patterns in `excludes` will be ignored.

    `depth` is how many directories deep to search (2 is the minimum in
    most situations).

    """

    start = time()

    cmd = ['find', dirpath,
           '-type', 'd',
           '-name', '.git',
           '-depth', str(depth)]

    output = subprocess.check_output(cmd)
    output = [os.path.dirname(s.strip()) for s in decode(output).split('\n')
              if s.strip()]

    results = []
    for filepath in output:
        ignore = False
        for pattern in excludes:
            if fnmatch(filepath, pattern):
                ignore = True
                break

        if ignore:
            continue

        results.append(filepath)
    log.debug('{} repos found in `{}` in {:0.2f} s'.format(len(results),
                                                           dirpath,
                                                           time() - start))
    return results


def main(wf):

    start = time()

    search_dirs = wf.settings.get('search_dirs', [])

    if not search_dirs:
        log.error('No search directories configured. '
                  'Nothing to update. Exiting.')
        return 0

    global_excludes = wf.settings.get('global_exclude_patterns', [])

    repos = []
    result_objs = []  # For AsyncResults objects returned by `apply_async`
    pool = Pool(CONCURRENT_SEARCHES)

    for data in search_dirs:
        dirpath = os.path.expanduser(data['path'])
        depth = data.get('depth', DEFAULT_DEPTH)
        excludes = data.get('excludes', []) + global_excludes

        if not os.path.exists(dirpath):
            log.error('Directory does not exist: {}'.format(dirpath))
            continue

        r = pool.apply_async(find_git_repos,
                             (dirpath, excludes, depth))
        result_objs.append(r)

    # Close the pool and wait for it to finish
    pool.close()
    pool.join()

    # Retrieve results
    for r in result_objs:
        repos += r.get()

    wf.cache_data('repos', repos)

    log.info('{} repos found in {:0.2f} s'.format(len(repos), time() - start))
    log.info('Update finished')

    return 0


if __name__ == '__main__':
    wf = Workflow()
    log = wf.logger
    decode = wf.decode
    sys.exit(wf.run(main))
