# TODO
# - Uit gaan van nieuw begroting en resultaat-sheet
# - Omzet prognose uit Simplicate
# - Begroot aantal mensen
# - Verzuim en vrije dagen uit Simplicate
# - Productiviteit uit Simplicate
# - Billable uit Simplicate
# - Top 3 klanten uit Simplicate of evt. yuki

# Algemeen
# - Script draaiend krijgen op de synology
# Productiviteit
#  - Effective rate= Bruto marge / alle declarabele uren (DDA: 96 bij een listprice van 103)
# Organisatie
# - FTE grafiek, ook begroot en vorig jaar
# - Vergelijking met de begroting per maand (Ik vind het een beetje jammer dat ik nu niet meer per maand met het opgestelde budget kan vergelijken, of kijk ik niet goed?)
# Serviceklant pagina
# - Wat een klant heeft uitgegeven
# - Chart per prio
# jira credentials in config.ini
#
# - Vergelijking met begroting
# - Geen sys.exit bij een fout maar fouten tonen in het dashboard

import sys
import os
import shutil
import subprocess

from model.caching import load_cache, clear_cache
from view.billable import render_billable_page
from view.dashboard import render_dashboard
from view.debiteuren import render_debiteuren_page
from view.sales import render_sales_page

# from view.service import render_service_page
# from view.service_issues import render_service_issues_page
from view.winstgevendheid import render_winstgevendheid_page
from view.klanten import render_klant_page
from view.tor import render_tor_page
from view.resultaat_berekening import render_resultaat_berekening
from view.budget import render_budget_status_page
from view.target import render_target_page

OUTPUT_FOLDER = 'output/'
DIRECTIE_FOLDER = '/Volumes/Downloads/hp/dashboard/'


def main():
    cd_to_script_path()
    initialize_cache()
    render_all_pages()
    copy_to_directie_folder()


def cd_to_script_path():
    path_to_go = os.path.dirname(__file__)
    if path_to_go:
        os.chdir(path_to_go)


def initialize_cache():
    for param in sys.argv[1:]:
        if param == '--nocache':
            clear_cache()
    load_cache()


def render_all_pages():
    # render the html pages
    render_sales_page()
    # render_service_page()
    # render_klant_page()
    # render_resultaat_vergelijking_page()
    render_debiteuren_page()
    # render_productiviteit_page()
    render_billable_page()
    render_winstgevendheid_page()
    # render_tor_page()
    # render_resultaat_berekening()
    # render_service_issues_page()
    # render_budget_status_page()
    # render_target_page()
    render_dashboard()


def copy_to_directie_folder():
    # De oplossing: Voeg /user/sbin/cron toe aan System Preferences -> Security & Privacy -> Full Disk Access
    # Alle files zie je in finder dialog met Option - Shift - Punt
    if not os.path.isdir(DIRECTIE_FOLDER):
        return

    print('Pushing to directie folder')
    for f in [f for f in os.listdir(OUTPUT_FOLDER)]:
        try_copy_file(OUTPUT_FOLDER + f, DIRECTIE_FOLDER + f)


def copytree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            print(f'{s} -> {d}')
            shutil.copy2(s, d)


def try_copy_file(source, destination):
    print(f'{source} -> {destination}')
    if os.path.isfile(source):
        try:
            shutil.copyfile(source, destination)
        except Exception as e:
            print(f'Error copying file {source} {str(e)}')
    else:
        copytree(source, destination)
        # try:
        #     copytree(source, destination)
        # except Error as e:
        #     print('Directory could not be not copied due to OS error. Error: %s' % e)


def doMount(host, share, mount_command='/sbin/mount_smbfs', protocol='', user='guest', password='', share_path=None):
    if password:
        password = ':' + password
    if not share_path:
        share_path = share
    result = subprocess.call(
        ['/sbin/ping', '-c', '1', '-t', '1', host], stdout=open(os.devnull, 'wb'), stderr=open(os.devnull, 'wb')
    )
    hostfound = not result
    if hostfound:
        message(f'Mounting shares on {host}')
    else:
        message(f'Host {host} not in reach', False)
    sharepath = "/Volumes/" + share

    if hostfound:
        if is_mounted(sharepath):
            # Host found and share is there: do nothing
            message(f'  Mount {share} already exists')
        else:
            # Host found but share is not there yet: mount
            message(f'  Mounting {share}')
            if not os.path.isdir(sharepath):
                os.mkdir(sharepath)
            endpoint = f'{protocol}//{user}{password}@{host}/{share_path}'
            message(mount_command, endpoint, sharepath)
            subprocess.call(
                [mount_command, endpoint, sharepath], stdout=open(os.devnull, 'wb'), stderr=open(os.devnull, 'wb')
            )
        return sharepath

    if is_mounted(sharepath):
        # Host not found but share is still there: unmount
        subprocess.call(
            ['/sbin/diskutil/unmount', sharepath],
            shell=True,
            stdout=open(os.devnull, 'wb'),
            stderr=open(os.devnull, 'wb'),
        )
    if os.path.isdir(sharepath):
        # Host not found but share folder is still there: remove it
        message(f'  Removing share {share}')
        subprocess.call(['rmdir', sharepath], stdout=open(os.devnull, 'wb'), stderr=open(os.devnull, 'wb'))
    return ''


def is_mounted(sharepath):
    mounts = subprocess.check_output(['/sbin/mount'], universal_newlines=True)
    return mounts.count('on ' + sharepath + ' ') > 0


def message(s='', ok=True, end='\n'):
    # from termcolor import colored
    # if not ok:
    #    s = colored(s, 'red', attrs=['bold'])
    print(s, end=end)


if __name__ == '__main__':
    main()
