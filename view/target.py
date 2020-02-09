import os
from datetime import datetime

from layout.basic_layout import headersize, midsize
from layout.block import HBlock, VBlock, TextBlock, Page
from layout.table import Table
from model.target import users_and_targets
from model.productiviteit import fraction_of_the_year_past
from layout.chart import StackedBarChart

groen = '#5c5'
blauw = '#55c'
rood = '#c55'
grijs = '#ccc'


def render_target_page():
    data = users_and_targets(datetime.today().year)  # .values.tolist()

    fraction = fraction_of_the_year_past()
    data['bereikt'] = data.apply(lambda row: round(min(row.result, row.target * fraction)), axis=1)
    data['onder_target'] = data.apply(lambda row: max(0, round(row.target * fraction - row.result)), axis=1)
    data['boven_target'] = data.apply(lambda row: max(0, round(row.result - row.target * fraction)), axis=1)
    data['rest'] = data.apply(lambda row: row.target - round(row.result - row.boven_target), axis=1)
    # data['colheaders'] =   data.apply( lambda row: f'{row.user} {round(row.result)} ({round((row.result/row.target/fraction-1)*100.0)}%)', axis=1)
    # target_now = [t[1]*fraction_of_the_year_past() for t in targets]

    # bereikt = [min(t[2],t[1]*) for t in targets]
    # onder_target = [min(0,t[1]*fraction_of_the_year_past()-t[2]) for t in targets]
    # boven_target = [min(0,t[2]-t[1]*fraction_of_the_year_past()) for t in targets]
    # nog_te_doen = [t[1]+max(t[2],t[1]*fraction_of_the_year_past()) for t in targets]
    namen = data['user'].tolist()
    bereikt = data['bereikt'].tolist()
    boven_target = data['boven_target'].tolist()
    onder_target = data['onder_target'].tolist()
    nog_te_doen = data['rest'].tolist()

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

    chart = StackedBarChart(
        800,
        840,
        '',
        ['bereikt', 'boven target', 'onder target', 'nog te doen'],
        [bereikt, boven_target, onder_target, nog_te_doen],
        [blauw, groen, rood, grijs],
        bottom_labels=namen,
        horizontal=True,
        data_labels=['', '', '', data_labels_js],
    )

    page = Page([TextBlock('Targets', headersize), VBlock([TextBlock('Per persoon met target en tot nu toe'), chart])])
    page.render('output/target.html')


if __name__ == '__main__':
    os.chdir('..')
    render_target_page()
