# TODO
# Algemeen
# - In Git
# - Script draaiend krijgen op de synology
# - Beter systeem ipv limited
# - Link property onderdeel maken van Block ipv van child
# Productiviteit
# - Vervangen door overzicht van billable uren per persoon. Met target.
#  - Billabe per tarief jr/mr/sr
#  - Effective rate= Bruto marge / alle declarabele uren (DDA: 96 bij een listprice van 103)
# Organisatie
# - Recruitment funnel
# - FTE grafiek, ook begroot en vorig jaar
# - Vergelijking met de begroting per maand (Ik vind het een beetje jammer dat ik nu niet meer per maand met het opgestelde budget kan vergelijken, of kijk ik niet goed?)

import sys
import os
import shutil
import subprocess

from model.caching import load_cache, clear_cache
from view.caching import render_detailpage
from view.dashboard import render_dashboard
from view.debiteuren import render_debiteuren_page
from view.productiviteit import render_productiviteit_page
from view.sales import render_sales_page
from view.service import render_service_page
from view.service_issues import render_service_issues_page
from view.winstgevendheid import render_winstgevendheid_page
from view.klanten import render_klant_page
from view.resultaat_vergelijking import render_resultaat_vergelijking_page
from view.tor import render_tor_page
from view.resultaat_berekening import render_resultaat_berekening
from view.budget import render_budget_status_page
from view.target import render_target_page

DIRECTIE_FOLDER = '/Volumes/Downloads/hp/dashboard/'
LIMITED_FOLDER = '/Volumes/Downloads/dashboard/'


def message(s='', ok=True, end='\n'):
    # from termcolor import colored
    # if not ok:
    #    s = colored(s, 'red', attrs=['bold'])
    print(s, end=end)


def is_mounted(sharepath):
    mounts = subprocess.check_output(['/sbin/mount'], universal_newlines=True)
    return mounts.count('on ' + sharepath + ' ') > 0


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


def main():
    # initialisation
    path_to_go = os.path.dirname(__file__)
    if path_to_go:
        os.chdir(path_to_go)
    for param in sys.argv[1:]:
        if param == '--nocache':
            clear_cache()
    load_cache()

    # render the html pages
    render_sales_page()
    render_service_page()
    render_klant_page()
    render_resultaat_vergelijking_page()
    render_debiteuren_page()
    # render_productiviteit_page()
    render_winstgevendheid_page()
    render_tor_page()
    # render_resultaat_berekening() # Wordt pas weer relevant na een aantal maanden
    render_service_issues_page()
    render_budget_status_page()
    render_target_page()
    render_dashboard()

    # De oplossing: Voeg /user/sbin/cron toe aan System Preferences -> Security & Privacy -> Full Disk Access
    if os.path.isdir(DIRECTIE_FOLDER):
        print('Pushing to directie folder')
        outfolder = f'{os.getcwd()}/output/'
        for f in os.listdir(outfolder):
            if f != 'limited':
                print(f'{outfolder} -> {DIRECTIE_FOLDER + f}')
                try:
                    shutil.copyfile(outfolder + f, DIRECTIE_FOLDER + f)
                except Exception as e:
                    print(f'Error copying {outfolder}{f} {str(e)}')
            if (
                f.split('.')[-1] in ('png', 'js', 'css') or f == 'login.html'
            ):  # Copy generic files to limited folder too
                shutil.copyfile(outfolder + f, 'output/limited/' + f)
    # copy the limited stuff to download.oberon.nl/dashboard
    if os.path.isdir(LIMITED_FOLDER):
        print('Pushing to team folder')
        for f in os.listdir(f'{outfolder}limited'):
            shutil.copyfile(f'{outfolder}limited/' + f, LIMITED_FOLDER + f)
    else:
        print(LIMITED_FOLDER, 'not found')


if __name__ == '__main__':
    main()
