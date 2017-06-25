#!/usr/bin/env python
# encoding: utf-8
#
# Copyright (c) 2014 deanishe@deanishe.net
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
# Created on 2014-07-04
#

"""Update the cache of git repositories.

Uses settings from the workflow's `settings.json` file.
"""

from __future__ import print_function, unicode_literals

import sys
import os
import subprocess
from fnmatch import fnmatch
from time import time
from multiprocessing.dummy import Pool

from workflow import Workflow3

from repos import Repo

# How many search threads to run at the same time
CONCURRENT_SEARCHES = 4

# How deep to search in the directory.
# 1 = look only in specified directory
# 2 = also look in subdirectories of specified directory
DEFAULT_DEPTH = 2

# Will be populated later
log = None
decode = None


def find_git_repos(dirpath, excludes, depth, name_for_parent=1):
    """Return list of directories containing a `.git` file or directory

    Results matching globbing patterns in `excludes` will be ignored.

    `depth` is how many directories deep to search (2 is the minimum in
    most situations).

    `name_for_parent` is which level of the directory hierarchy to name
    the repo after relative to `.git` (1=immediate parent, 2=grandparent)

    """
    start = time()

    cmd = ['find', '-L', dirpath,
           '-name', '.git',
           '-maxdepth', str(depth)]

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

        # Work out name for repo
        if name_for_parent < 2:  # ignore 0, it's pointless
            name = os.path.basename(filepath)
        else:
            components = filepath.rstrip('/').split('/')
            if name_for_parent >= len(components):
                log.warning(u'%s : `name_for_parent` is %d, but '
                            u'only %d levels in file tree',
                            filepath, name_for_parent, len(components))
                name = os.path.basename(filepath)
            else:
                name = components[-(name_for_parent)]

        results.append(Repo(name, filepath))

    log.debug(u'%d repo(s) found in `%s` in %0.2fs', len(results), dirpath,
              time() - start)

    for r in results:
        log.debug('    %r', r)

    return results


def main(wf):
    """Run script."""
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
        name_for_parent = data.get('name_for_parent', 1)

        if not os.path.exists(dirpath):
            log.error(u'directory does not exist: %s', dirpath)
            continue

        r = pool.apply_async(find_git_repos,
                             (dirpath, excludes, depth, name_for_parent))
        result_objs.append(r)

    # Close the pool and wait for it to finish
    pool.close()
    pool.join()

    # Retrieve results
    for r in result_objs:
        repos += r.get()

    wf.cache_data('repos', repos)

    log.info('%d repo(s) found in %0.2fs', len(repos), time() - start)
    log.info('update finished')
    [h.flush() for h in log.handlers]

    return 0


if __name__ == '__main__':
    wf = Workflow3()
    log = wf.logger
    decode = wf.decode
    sys.exit(wf.run(main))
