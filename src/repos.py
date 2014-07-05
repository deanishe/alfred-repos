#!/usr/bin/env python
# encoding: utf-8
#
# Copyright © 2013 deanishe@deanishe.net.
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
# Created on 2013-11-04
#

"""repos.py [options] [<query>] [<appnum>] [<path>]

Find, open and search Git repos on your system.

Usage:
    repos.py [<query>]
    repos.py (-e|--edit)
    repos.py --helpfile
    repos.py --update
    repos.py --open <appnum> <path>

Options:
    --update        Update database of Git repos
    --open          Open path in specified app
    -e, --edit      Open settings file
    -h, --help      Show this message
    --helpfile      Open included help file

"""

from __future__ import print_function, unicode_literals

import sys
import os
import subprocess

from workflow import Workflow, ICON_WARNING, ICON_INFO
from workflow.background import is_running, run_in_background


UPDATE_INTERVAL = 3600 * 3  # 3 hours


DEFAULT_SETTINGS = {
    'search_dirs': [{
        'path': '~/delete/this/example',
        'depth': 2,
        'excludes': ['tmp', 'bad/smell/*']
    }],
    'global_exclude_patterns': [],
    'app_1': 'Finder',
    'app_2': 'Terminal',
    'app_3': None,
    'app_4': None,
    'app_5': None,
    'app_6': None,
}

# Will be populated later
log = None


def main(wf):
    from docopt import docopt

    # Create settings file with default settings if it doesn't exist
    if not os.path.exists(wf.settings_path):
        for key in DEFAULT_SETTINGS:
            wf.settings[key] = DEFAULT_SETTINGS[key]

    # Handle arguments
    #-------------------------------------------------------------------
    args = docopt(__doc__, wf.args)

    log.debug('args: {}'.format(args))

    query = args.get('<query>')
    path = args.get('<path>')
    appnum = args.get('<appnum>')
    if appnum:
        appnum = int(appnum)

    apps = {}
    for i in range(1, 6):
        apps[i] = wf.settings.get('app_{}'.format(i))

    if not apps.get(1):  # Things will break if this isn't set
        apps[1] = 'Finder'

    # Alternate actions
    #-------------------------------------------------------------------
    if appnum and path:
        app = apps.get(appnum)
        if app is None:
            print('App {} not set. Use `reposettings`'.format(appnum))
            return 0
        else:
            subprocess.call(['open', '-a', app, path])
            return 0

    elif args.get('--edit'):
        subprocess.call(['open', wf.settings_path])
        return 0

    elif args.get('--update'):
        run_in_background('update', ['/usr/bin/python', 'update.py'])
        return 0

    # Try to search git repos
    #-------------------------------------------------------------------
    search_dirs = wf.settings.get('search_dirs', [])

    # Can't do anything with not directories to search
    if not search_dirs or wf.settings == DEFAULT_SETTINGS:
        wf.add_item("You haven't configured any directories to search",
                    'Use `reposettings` to edit your configuration',
                    icon=ICON_WARNING)
        wf.send_feedback()
        return 0

    # Load data, update if necessary
    if not wf.cached_data_fresh('repos', max_age=UPDATE_INTERVAL):
        run_in_background('update', ['/usr/bin/python', 'update.py'])

    repos = wf.cached_data('repos', max_age=0)

    # Show appropriate warning/info message if there are no repos to
    # show/search
    #-------------------------------------------------------------------
    if not repos:
        if is_running('update'):
            wf.add_item('Initialising database of repos…',
                        'Should be done in a few seconds',
                        icon=ICON_INFO)
        else:
            wf.add_item('No known git repos',
                        'Check your settings with `reposettings`',
                        icon=ICON_WARNING)
        wf.send_feedback()
        return 0

    # Perform search and send results to Alfred
    #-------------------------------------------------------------------

    # Set modifier subtitles
    modifier_subtitles = {}
    i = 2
    for mod in ('cmd', 'alt', 'ctrl', 'shift', 'fn'):
        if not apps.get(i):
            modifier_subtitles[mod] = (
                'App {} not set. Use `reposettings` to set it.'.format(i))
        else:
            modifier_subtitles[mod] = 'Open in {}'.format(apps[i])
        i += 1

    if query:
        repos = wf.filter(query, repos,
                          lambda p: os.path.basename(p),
                          min_score=30)

    if not repos:
        wf.add_item('No matching repos found', icon=ICON_WARNING)

    for path in repos:
        wf.add_item(os.path.basename(path),
                    path.replace(os.environ['HOME'], '~'),
                    modifier_subtitles=modifier_subtitles,
                    arg=path,
                    valid=True,
                    type='file',
                    icon='icon.png')

    wf.send_feedback()
    return 0


if __name__ == '__main__':
    wf = Workflow()
    log = wf.logger
    sys.exit(wf.run(main))
