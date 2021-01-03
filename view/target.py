import os
from datetime import datetime

from layout.basic_layout import headersize, midsize
from layout.block import TextBlock, Page, HBlock
from model.target import users_and_targets
from model.utilities import fraction_of_the_year_past
from layout.chart import StackedBarChart, ChartConfig

groen = '#5c5'
blauw = '#55c'
rood = '#c55'
grijs = '#ccc'


def render_target_page():
    data = users_and_targets(datetime.today().year)  # .values.tolist()

    page = Page(
        [
            TextBlock('Targets', headersize),
            TextBlock('Per persoon met target en tot nu toe'),
            targets_chart(data, 800, 840),
            totalen_block(data),
        ]
    )

    page.render('output/target.html')


def targets_chart(data, width, height):

    if not len(data):
        return TextBlock('No targets data for targets_chart')
    # fraction = fraction_of_the_year_past()
    # Pandas operaties op de hele lijst tegelijk
    data['fraction_of_the_year'] = data.apply(lambda row: fraction_of_the_year_past(row.start_day), axis=1)
    data['bereikt'] = data.apply(lambda row: round(min(row.result, row.target * row.fraction_of_the_year)), axis=1)
    data['onder_target'] = data.apply(
        lambda row: max(0, round(row.target * row.fraction_of_the_year - row.result)), axis=1
    )
    data['boven_target'] = data.apply(
        lambda row: max(0, round(row.result - row.target * row.fraction_of_the_year)), axis=1
    )
    data['rest'] = data.apply(lambda row: round(row.target - row.onder_target - row.bereikt - row.boven_target), axis=1)

    # Maak er lijsten van t.b.v. de grafiek
    namen = data['user'].tolist()
    bereikt = data['bereikt'].tolist()
    boven_target = data['boven_target'].tolist()
    onder_target = data['onder_target'].tolist()
    nog_te_doen = data['rest'].tolist()

    # Wat specifieke chart.js code om de getalletjes in de balken te krijgen in de grafiek
    data_labels_js = '''{
        color: '#FFFFFF',
        anchor : 'start',
        align: 'right',
        formatter: function(value, context) {
            bereikt = context.chart.data.datasets[0].data[context.dataIndex];
            boven_target = context.chart.data.datasets[1].data[context.dataIndex];
            onder_target = context.chart.data.datasets[2].data[context.dataIndex];
            label = (bereikt+boven_target) + '/' + (bereikt+onder_target) + ' (';
            if (boven_target > 0) { label += '+' + Math.round(100*boven_target/bereikt) + '%' };
            if (onder_target > 0) { label += '-' + Math.round(100*onder_target/(onder_target+bereikt)) + '%' };
            label += ')';
            return label;
        }
    }'''

    return StackedBarChart(
        [bereikt, boven_target, onder_target, nog_te_doen],
        ChartConfig(
            width=width,
            height=height,
            labels=['bereikt', 'boven target', 'onder target', 'nog te doen'],
            colors=[blauw, groen, rood, grijs],
            bottom_labels=namen,
            horizontal=True,
            data_labels=['', '', '', data_labels_js],
        ),
    )


def totalen_block(data):
    # Totalen
    totaal_result = data['result'].sum()
    totaal_target = data['target'].sum() * fraction_of_the_year_past()
    totaal_boven_target = totaal_result - totaal_target
    totaal_percentueel = totaal_result / totaal_target * 100 - 100 if totaal_target else 0

    return HBlock(
        [
            TextBlock(f'Totaal t.o.v. target', color='gray'),
            TextBlock(totaal_boven_target, midsize, format='+'),
            TextBlock('uur', color='gray'),
            TextBlock(totaal_percentueel, midsize, format='+%'),
        ]
    )


if __name__ == '__main__':
    os.chdir('..')
    render_target_page()
