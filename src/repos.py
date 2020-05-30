#!/usr/bin/env python
# encoding: utf-8
#
# Copyright (c) 2013 deanishe@deanishe.net.
# MIT Licence. See http://opensource.org/licenses/MIT
#
# Created on 2013-11-04
#

"""repos.py [command] [options] [<query>] [<path>]

Find, open and search Git repos on your system.

Usage:
    repos.py search [<query>]
    repos.py settings
    repos.py update
    repos.py open <appkey> <path>

Options:
    -h, --help      Show this message

"""

from __future__ import print_function

from collections import namedtuple
import os
import re
import subprocess
import sys
import time

from workflow import Workflow3, ICON_WARNING, ICON_INFO
from workflow.background import is_running, run_in_background
from workflow.update import Version


# How often to check for new/updated repos
DEFAULT_UPDATE_INTERVAL = 180  # minutes

# GitHub repo for self-updating
UPDATE_SETTINGS = {'github_slug': 'deanishe/alfred-repos'}

# GitHub Issues
HELP_URL = 'https://github.com/deanishe/alfred-repos/issues'

# Icon shown if a newer version is available
ICON_UPDATE = 'update-available.png'

# Available modifier keys
# MODIFIERS = ('cmd', 'alt', 'ctrl', 'shift', 'fn')

# These apps will be passed the remote repo URL instead
# of the local directory path
BROWSERS = [
    'Browser',  # default browser
    'Google Chrome',
    'Firefox',
    'Safari',
    'WebKit',
]

DEFAULT_SEARCH_PATH = '~/delete/this/example'
DEFAULT_SETTINGS = {
    'search_dirs': [{
        'path': DEFAULT_SEARCH_PATH,
        'depth': 2,
        'name_for_parent': 1,
        'excludes': ['tmp', 'bad/smell/*']
    }],
    'global_exclude_patterns': [],
    'app_default': 'Finder',
    'app_cmd': 'Terminal',
    'app_alt': None,
    'app_ctrl': None,
    'app_shift': None,
    'app_fn': None,
}

# Will be populated later
log = None


Repo = namedtuple('Repo', 'name path')


class AttrDict(dict):
    """Access dictionary keys as attributes."""

    def __init__(self, *args, **kwargs):
        """Create new dictionary."""
        super(AttrDict, self).__init__(*args, **kwargs)
        # Assigning self to __dict__ turns keys into attributes
        self.__dict__ = self


def migrate_v1_config():
    """Replace v1 format in settings with v2 format.

    Change numbered apps to named apps.
    """
    log.debug('migrating v1 config to v2 ...')
    newkeys = {
        '1': 'default',
        '2': 'cmd',
        '3': 'alt',
        '4': 'ctrl',
        '5': 'shift',
        '6': 'fn',
    }
    for k, nk in newkeys.items():
        wf.settings['app_' + nk] = wf.settings.get('app_' + k)
        try:
            del wf.settings['app_' + k]
            log.debug('changed `app_%s` to `app_%s`', k, nk)
        except KeyError:
            pass


def is_defaults(d):
    """Return ``True`` if settings are do-nothing defaults.

    Args:
        d (dict): Workflow settings
    """
    dirs = d.get('search_dirs') or []
    return len(dirs) == 1 and dirs[0]['path'] == DEFAULT_SEARCH_PATH


def settings_updated():
    """Test whether settings file is newer than repos cache.

    Returns:
        bool: ``True`` if ``settings.json`` is newer than the repos cache.

    """
    cache_age = wf.cached_data_age('repos')
    settings_age = time.time() - os.stat(wf.settings_path).st_mtime
    log.debug('cache_age=%0.2f, settings_age=%0.2f', cache_age, settings_age)
    return settings_age < cache_age


def join_english(items):
    """Join a list of unicode objects with commas and/or 'and'."""
    if isinstance(items, unicode):
        return items

    if len(items) == 1:
        return unicode(items[0])

    elif len(items) == 2:
        return u' and '.join(items)

    return u', '.join(items[:-1]) + u' and {}'.format(items[-1])


def get_apps():
    """Load applications configured in settings.

    Each value may be a string for a single app or a list for
    multiple apps.

    Returns:
        dict: Modkey to application mapping.

    """
    apps = {}
    for key, app in wf.settings.items():
        if not key.startswith('app_'):
            continue

        key = key[4:]
        if isinstance(app, list):
            app = app[:]
        apps[key] = app

    if not apps.get('default'):  # Things will break if this isn't set
        apps['default'] = u'Finder'

    return apps


def get_repos(opts):
    """Load repos from cache, triggering an update if necessary.

    Args:
        opts (AttrDict): CLI options

    Returns:
        list: Sequence of `Repo` tuples.

    """
    # Load data, update if necessary
    if not wf.cached_data_fresh('repos', max_age=opts.update_interval):
        do_update()
    repos = wf.cached_data('repos', max_age=0)

    if not repos:
        do_update()
        return []

    # Check if cached data is old version
    if isinstance(repos[0], basestring):
        do_update()
        return []

    return repos


def repo_url(path):
    """Return repo URL extracted from `.git/config`.

    Args:
        path (str): Path to git repo.

    Returns:
        str: URL of remote/origin.

    """
    url = subprocess.check_output(['git', 'config', 'remote.origin.url'],
                                  cwd=path)
    url = re.sub(r'(^.+@)|(^https://)|(^git://)|(.git$)', '', url)
    return 'https://' + re.sub(r':', '/', url).strip()


def do_open(opts):
    """Open repo in the specified application(s).

    Args:
        opts (AttrDict): CLI options.

    Returns:
        int: Exit status.

    """
    all_apps = get_apps()
    apps = all_apps.get(opts.appkey)
    if apps is None:
        print('App {} not set. Use `reposettings`'.format(opts.appkey))
        return 0

    if not isinstance(apps, list):
        apps = [apps]

    for app in apps:
        if app in BROWSERS:
            url = repo_url(opts.path)
            log.info('opening %s with %s ...', url, app)
            if app == 'Browser':
                subprocess.call(['open', url])
            else:
                subprocess.call(['open', '-a', app, url])
        else:
            log.info('opening %s with %s ...', opts.path, app)
            subprocess.call(['open', '-a', app, opts.path])


def do_settings():
    """Open ``settings.json`` in default editor.

    Args:
        opts (AttrDict): CLI options.

    Returns:
        int: Exit status.

    """
    subprocess.call(['open', wf.settings_path])
    return 0


def do_update():
    """Update cached list of git repos.

    Args:
        opts (AttrDict): CLI options.

    Returns:
        int: Exit status.

    """
    run_in_background('update', ['/usr/bin/python', 'update.py'])
    return 0


def do_search(repos, opts):
    """Filter list of repos and show results in Alfred.

    Args:
        repos (list): Sequence of ``Repo`` tuples.
        opts (AttrDict): CLI options.

    Returns:
        int: Exit status.

    """
    apps = get_apps()
    subtitles = {}
    valid = {}
    for key, app in apps.items():
        if not app:
            subtitles[key] = ('App for ' + key + ' not set. '
                              'Use `reposettings` to set it.')
            valid[key] = False
        else:
            subtitles[key] = u'Open in {}'.format(join_english(app))
            valid[key] = True

    if opts.query:
        repos = wf.filter(opts.query, repos, lambda t: t[0], min_score=30)
        log.info(u'%d/%d repos match `%s`', len(repos), len(repos), opts.query)

    if not repos:
        wf.add_item('No matching repos found', icon=ICON_WARNING)

    home = os.environ['HOME']
    for r in repos:
        log.debug(r)
        pretty_path = subtitle = r.path.replace(home, '~')
        app = subtitles.get('default')
        if app:
            subtitle += ' //  ' + app
        it = wf.add_item(
            r.name,
            subtitle,
            arg=r.path,
            uid=r.path,
            valid=valid.get('default', False),
            type='file',
            icon='icon.png'
        )
        it.setvar('appkey', 'default')

        for key in apps:
            if key == 'default':
                continue
            mod = it.add_modifier(key.replace('_', '+'),
                                  pretty_path + '  //  ' + subtitles[key],
                                  arg=r.path, valid=valid[key])
            mod.setvar('appkey', key)

    wf.send_feedback()
    return 0


def parse_args():
    """Extract options from CLI arguments.

    Returns:
        AttrDict: CLI options.

    """
    from docopt import docopt

    args = docopt(__doc__, wf.args)

    log.debug('args=%r', args)

    update_interval = int(os.getenv('UPDATE_EVERY_MINS',
                                    DEFAULT_UPDATE_INTERVAL)) * 60

    opts = AttrDict(
        query=(args.get('<query>') or u'').strip(),
        path=args.get('<path>'),
        appkey=args.get('<appkey>') or 'default',
        update_interval=update_interval,
        do_search=args.get('search'),
        do_update=args.get('update'),
        do_settings=args.get('settings'),
        do_open=args.get('open'),
    )

    log.debug('opts=%r', opts)
    return opts


def main(wf):
    """Run the workflow."""
    # Update settings format
    if wf.last_version_run and wf.last_version_run < Version('2'):
        migrate_v1_config()

    opts = parse_args()

    # Alternate actions
    # ------------------------------------------------------------------
    if opts.do_open:
        return do_open(opts)

    elif opts.do_settings:
        return do_settings()

    elif opts.do_update:
        return do_update()

    # Notify user if update is available
    # ------------------------------------------------------------------
    if wf.update_available:
        wf.add_item(u'Workflow Update is Available',
                    u'↩ or ⇥ to install',
                    autocomplete='workflow:update',
                    valid=False,
                    icon=ICON_UPDATE)

    # Try to search git repos
    # ------------------------------------------------------------------
    search_dirs = wf.settings.get('search_dirs', [])

    # Can't do anything with no directories to search
    if not search_dirs or is_defaults(wf.settings):
        wf.add_item("You haven't configured any directories to search",
                    'Use `reposettings` to edit your configuration',
                    icon=ICON_WARNING)
        wf.send_feedback()
        return 0

    # Reload repos if settings file has been updated
    if settings_updated():
        log.info('settings were updated. Reloading repos...')
        do_update()

    repos = get_repos(opts)

    # Show appropriate warning/info message if there are no repos to
    # show/search
    # ------------------------------------------------------------------
    if not repos:
        if is_running('update'):
            wf.add_item(u'Updating list of repos…',
                        'Should be done in a few seconds',
                        icon=ICON_INFO)
            wf.rerun = 0.5
        else:
            wf.add_item('No git repos found',
                        'Check your settings with `reposettings`',
                        icon=ICON_WARNING)
        wf.send_feedback()
        return 0

    # Reload results if `update` is running
    if is_running('update'):
        wf.rerun = 0.5

    return do_search(repos, opts)


if __name__ == '__main__':
    wf = Workflow3(default_settings=DEFAULT_SETTINGS,
                   update_settings=UPDATE_SETTINGS,
                   help_url=HELP_URL)
    log = wf.logger
    sys.exit(wf.run(main))
