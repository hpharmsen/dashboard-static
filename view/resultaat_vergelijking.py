import os
from settings import get_output_folder
from layout.basic_layout import MID_SIZE, HEADER_SIZE
from layout.block import VBlock, TextBlock, Page
from model.resultaat_vergelijking import (
    omzet_per_maand,
    omzet_begroot_per_maand,
    omzet_vorig_jaar_per_maand,
    winst_per_maand,
    winst_begroot_per_maand,
    winst_vorig_jaar_per_maand,
    MAANDEN,
)
from layout.chart import LineChart, ChartConfig


def render_resultaat_vergelijking_page():

    omzet = VBlock(
        [
            TextBlock('Omzet vergelijking', MID_SIZE),
            LineChart(
                [omzet_per_maand(), omzet_begroot_per_maand(), omzet_vorig_jaar_per_maand()],
                ChartConfig(
                    width=900,
                    height=600,
                    labels=["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
                    colors=['#4285f4', '#f4b400', '#db4437'],
                    bottom_labels=['Omzet', 'Omzet begroot', 'Omzet vorig jaar'],
                ),
            ),
        ]
    )

    winst = VBlock(
        [
            TextBlock('Winst vergelijking', MID_SIZE),
            LineChart(
                [winst_per_maand(), winst_begroot_per_maand(), winst_vorig_jaar_per_maand()],
                ChartConfig(
                    width=900,
                    height=600,
                    labels=MAANDEN,
                    colors=['#4285f4', '#f4b400', '#db4437'],
                    bottom_labels=['Winst', 'Winst begroot', 'Winst vorig jaar'],
                ),
            ),
        ]
    )

    page = Page([TextBlock('Resultaat', HEADER_SIZE), VBlock([omzet, winst])])

    page.render('output/resultaat_vergelijking.html')


if __name__ == '__main__':
    os.chdir('..')
    render_resultaat_vergelijking_page(get_output_folder())
