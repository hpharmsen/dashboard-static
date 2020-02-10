import re
import random
import string
from typing import NamedTuple, List

from layout.block import Block

id_pattern = re.compile('[\W_]+')


def randomString(stringLength=3):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))


class ChartConfig(NamedTuple):
    width: int
    height: int
    title: str = ''
    labels: List = []  # Legend labels
    colors: List = []
    bg_color: str = '#ffffff'
    link: str = None
    bottom_labels: List = []  # for Bar, StackedBar and Line
    data_labels: List = []  # Labels for in the chart itself. Currently only implemented for StackedBarChart
    max_y_axis: float = None  # Currently only for StackedBarChart and ScatterChart
    min_y_axis: float = None  # Currently only for ScatterChart
    horizontal: bool = False  # Currently only for StackedBarChart
    x_type: str = 'float'  # Currently only for ScatterChart


class Chart(Block):
    def __init__(self, values, config, limited=False):
        id = id_pattern.sub('', config.title) + '_' + randomString()
        super().__init__(
            id=id, width=config.width, height=config.height, bg_color=config.bg_color, link=config.link, limited=limited
        )
        self.datasets = f'''[{{
                    data: {str(values)},
                    backgroundColor: {str(config.colors)},
                    label: ''
                }}]'''  #!! Moet backgroundColor niet config.bg_color zijn??
        self.values = values
        self.config = config
        self.labels = config.labels  # Can be overwritten
        self.canvas_height_difference = 150  # Difference between div height and canvas height, can be overwritten

    def do_render(self, left, top, position):
        data = f'''{{
                datasets: {self.datasets},
                labels: {str(self.labels)}
            }}'''

        return f'''<div style="position:{position}; left:{left}px; top:{top}px; width:{self.width}px; height:{self.height}px; background-color:{self.bg_color}">
		        <canvas id="{self.id}_canvas" width="{self.width}px" height="{self.height-self.canvas_height_difference}px"></canvas>
            </div>
        
            <script>
                Chart.plugins.unregister(ChartDataLabels); // To make sure not all charts show labels automatically
                window.addEventListener('load',  function() {{
                    var ctx_{self.id} = document.getElementById('{self.id}_canvas').getContext('2d');
                    window.{self.id}Chart = new Chart(ctx_{self.id}, {{
                        type: '{self.type}', 
                        data: {data}, 
                        //plugins: [ChartDataLabels], // Add this line to enable data labels for this chart
                        options: {self.options}
                    }});
                }})
        
            </script>'''

    def render(self, align='', limited=False):
        if self.limited and limited:
            return ''
        return self.do_render(0, 0, 'relative')

    def render_absolute(self, left, top, limited=False):
        if self.limited and limited:
            return ''
        return self.do_render(left, top, 'absolute')


class PieChart(Chart):
    def __init__(self, values, config, limited=False):
        super().__init__(values, config, limited)

        self.type = 'doughnut'
        self.options = f'''{{
                responsive: true,
                legend: {{
                    position: 'top',
                }},
                title: {{
                    display: false
                }},
                animation: {{
                    animateScale: true,
                    animateRotate: true
                }},
                cutoutPercentage: 30
        }}'''


class BarChart(Chart):
    def __init__(self, values, config, limited=False):
        super().__init__(values, config, limited)

        self.type = 'bar'

        self.datasets = '['
        for label, value, color in zip(config.bottom_labels, values, config.colors):
            self.datasets += f'''{{
                                    label: '{label}',
                                    data: {value},
                                    backgroundColor: '{color}'
                                  }},'''
        self.datasets = self.datasets[:-1] + ']'

        self.options = f'''{{
            title: {{
                display: false
            }},
            scales: {{
                xAxes: [{{
                    categoryPercentage: 0.9,
                    barPercentage: 0.9
                }}],
                yAxes: [{{
                    ticks: {{
                        min:0,
                    }}
                }}]
            }}
        }}'''

    def render(self, align='', limited=False):
        return super().render(align, limited)

    def render_absolute(self, left, top, limited=False):
        return super().render_absolute(left, top, limited)


class StackedBarChart(Chart):
    def __init__(self, values, config, limited=False):
        super().__init__(values, config, limited)

        self.type = 'horizontalBar' if config.horizontal else 'bar'

        # Make datalabels as long as the rest, set a default and replace default where it was specified in data_labels param
        dl = ['{display: false }'] * len(values)
        for i, val in enumerate(config.data_labels):
            if val:
                dl[i] = val

        self.datasets = '['
        for label, value, color, dls in zip(config.labels, self.values, config.colors, dl):
            if type(value) != type([]):
                value = [value]
            self.datasets += f'''{{
                                    label: '{label}',
                                    data: {value},
                                    backgroundColor: '{color}',
                                    datalabels: {dls} 
                                  }},'''
        self.datasets = self.datasets[:-1] + ']'
        bottom_labels = config.bottom_labels if config.bottom_labels else [config.title]
        bottom_label_string = "', '".join(bottom_labels)
        self.labels = f"['{bottom_label_string}']"
        ticks = f',ticks: {{max: {config.max_y_axis}}}' if config.max_y_axis else ''
        self.options = f'''{{
                title: {{
                    display: false
                }},
            scales: {{
                xAxes: [{{stacked: true}}],
                yAxes: [{{stacked: true {ticks}}}]
            }}
        }}'''


class LineChart(Chart):
    def __init__(self, values, config, limited=False):
        super().__init__(values, config, limited)

        self.type = 'line'
        self.datasets = '['
        for label, value, color in zip(config.bottom_labels, values, config.colors):
            self.datasets += f'''{{
                                    label: '{label}',
                                    data: {value},
                                    backgroundColor: '{color}', 
                                    borderColor: '{color}',
                                    fill: false, 
                                  }},'''
        self.datasets = self.datasets[:-1] + ']'
        # self.labels = config.labels

        self.options = f'''{{
                title: {{
                    display: false
                }},
            scales: {{
                xAxes: [{{
                    categoryPercentage: 0.9,
                    barPercentage: 0.9
                }}],
                yAxes: [{{
                    ticks: {{
                        min:0,
                    }}
                }}]
            }}
        }}'''


BORDER_COLOR = 0
FILL_COLOR = 1


class ScatterChart(Chart):
    def __init__(self, values, config, limited=False):
        super().__init__(values, config, limited)

        self.type = 'line'
        self.datasets = '['
        if config.x_type == 'date':
            valuestr = '['
            for v in values:
                valuestr += f"{{ 'x':'{v['x']}', 'y': {v['y']} }}, "
            valuestr = valuestr[:-2] + ']'
        else:
            valuestr = values
        self.datasets += f'''{{
                                label: '{config.title}',
                                data: {valuestr},
                                borderColor: '{config.colors[BORDER_COLOR]}',
                                backgroundColor: '{config.colors[FILL_COLOR]}',
                                borderWidth: 1, 
                                fill: true, 
                              }},'''
        self.datasets = self.datasets[:-1] + ']'
        # self.labels = []
        self.canvas_height_difference = 0  # Is for scatter chart other than for other chart types

        ymin = '' if config.min_y_axis == None else f'suggestedMin: {config.min_y_axis},'
        ymax = '' if config.max_y_axis == None else f'max: {config.max_y_axis},'
        self.options = f'''{{
            title: {{
                display: false
            }},
            legend: {{
                display: false
            }},
            elements: {{
                point:{{
                    radius: 0
                }}
            }},
            scales: {{
                xAxes: [{{
                    type: 'time',
                    position: 'bottom',
                    time: {{
						parser: 'YYYY-MM-DD'
					}},
                    ticks: {{
                        fontSize:9
                    }},
					scaleLabel: {{
						display: true
					}}
                }}],      
                yAxes: [{{
                    ticks: {{
                        maxTicksLimit: 3,
                        fontSize:9,
                        {ymin}
                        {ymax}
                    }}
                }}]      
            }}
        }}'''
