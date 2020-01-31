import os
from model.resultaat import omzet_per_klant_laatste_zes_maanden
from model.winstgevendheid import winst_per_klant
from layout.basic_layout import headersize, midsize
from layout.block import HBlock, VBlock, TextBlock, Table, Page


def render_klant_page():

    omzet = VBlock(
        [
            TextBlock('Omzet laatste 6 maanden', midsize),
            Table(omzet_per_klant_laatste_zes_maanden(), aligns=['left', 'right', 'right'], formats=['', '€', '%']),
        ]
    )

    # winst = VBlock(
    #     [
    #         TextBlock('Winstgevendheid', midsize),
    #         Table(
    #             winst_per_klant(),
    #             id="winst_per_klant",
    #             headers=['klant', 'uren', 'gefactureerd', 'kosten', 'winst'],
    #             aligns=['left', 'right', 'right', 'right', 'right'],
    #             formats=['', '.', '€', '€', '€'],
    #         ),
    #     ],
    #     limited=True,
    # )

    page = Page([TextBlock('Klanten', headersize), omzet])
    page.render('output/clients.html')
    page.render('output/limited/clients.html', limited=1)


if __name__ == '__main__':
    os.chdir('..')
    render_klant_page()
