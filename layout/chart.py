import re
import random
import string
from layout.block import Block

pattern = re.compile('[\W_]+')


def randomString(stringLength=3):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))


class Chart(Block):
    def __init__(self, width, height, title, labels, values, colors, bg_color='', limited=False, link=None):
        super().__init__(id=id, width=width, height=height, bg_color=bg_color, limited=limited, link=link)
        self.id = pattern.sub('', title) + '_' + randomString()
        self.title = title
        self.labels = labels
        self.values = values
        self.colors = colors
        self.datasets = f'''[{{
                    data: {str(self.values)},
                    backgroundColor: {str(self.colors)},
                    label: ''
                }}]'''
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
    def __init__(self, width, height, title, labels, values, colors, bg_color='', limited=False):
        super().__init__(width, height, title, labels, values, colors, bg_color, limited)

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
    def __init__(self, width, height, title, labels, values, colors, bg_color='', bottom_labels=[], limited=False):
        super().__init__(width, height, title, labels, values, colors, bg_color, limited)

        self.type = 'bar'

        self.datasets = '['
        for label, value, color in zip(bottom_labels, self.values, self.colors):
            self.datasets += f'''{{
                                    label: '{label}',
                                    data: {value},
                                    backgroundColor: '{color}'
                                  }},'''
        self.datasets = self.datasets[:-1] + ']'
        self.labels = labels

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
    def __init__(
        self,
        width,
        height,
        title,
        labels,
        values,
        colors,
        bg_color='',
        bottom_label='',
        horizontal=False,
        max_axis_value=None,
        data_labels=[],
        limited=False,
        link = None
    ):
        super().__init__(width, height, title, labels, values, colors, bg_color, limited, link)

        self.type = 'horizontalBar' if horizontal else 'bar'

        # Make datalabels as long as the rest, set a default and replace default where it was specified in data_labels param
        dl = ['{display: false }'] * len(values)
        for i, val in enumerate(data_labels):
            if val:
                dl[i] = val

        self.datasets = '['
        for label, value, color, dls in zip(self.labels, self.values, self.colors, dl):
            if type(value) != type([]):
                value = [value]
            self.datasets += f'''{{
                                    label: '{label}',
                                    data: {value},
                                    backgroundColor: '{color}',
                                    datalabels: {dls} 
                                  }},'''
        self.datasets = self.datasets[:-1] + ']'
        if not bottom_label:
            bottom_label = title
        elif type(bottom_label) == type([]):
            bottom_label = "', '".join(bottom_label)
        self.labels = f"['{bottom_label}']"
        ticks = f',ticks: {{max: {max_axis_value}}}' if max_axis_value else ''
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
    def __init__(self, width, height, title, labels, values, colors, bg_color='', bottom_labels=[], limited=False):
        super().__init__(width, height, title, labels, values, colors, bg_color, limited)

        self.type = 'line'
        self.datasets = '['
        for label, value, color in zip(bottom_labels, self.values, self.colors):
            self.datasets += f'''{{
                                    label: '{label}',
                                    data: {value},
                                    backgroundColor: '{color}', 
                                    borderColor: '{color}',
                                    fill: false, 
                                  }},'''
        self.datasets = self.datasets[:-1] + ']'
        self.labels = labels

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


class ScatterChart(Chart):
    def __init__(
        self,
        width,
        height,
        title='',
        label='',
        value=0,
        color='#66666',
        bg_color='#ffffff',
        fill_color='#ddeeff',
        limited=False,
        x_type='float',
        y_start=None,
        y_max=None,
    ):
        super().__init__(width, height, title, [label], [value], [color], bg_color, limited)

        self.type = 'line'
        self.datasets = '['
        if x_type == 'date':
            valuestr = '['
            for v in value:
                valuestr += f"{{ 'x':'{v['x']}', 'y': {v['y']} }}, "
            valuestr = valuestr[:-2] + ']'
        else:
            valuestr = value
        self.datasets += f'''{{
                                label: '{label}',
                                data: {valuestr},
                                borderColor: '{color}',
                                backgroundColor: '{fill_color}',
                                borderWidth: 1, 
                                fill: true, 
                              }},'''
        self.datasets = self.datasets[:-1] + ']'
        self.labels = []
        self.canvas_height_difference = 0  # Is for scatter chart other than for other chart types

        ymin = '' if y_start == None else f'suggestedMin: {y_start},'
        ymax = '' if y_max == None else f'max: {y_max},'
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
