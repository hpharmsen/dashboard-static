import random
import re
import string
from typing import NamedTuple, List

from layout.block import Block

id_pattern = re.compile("[\W_]+")


def randomString(stringLength=3):
    """Generate a random string of fixed length"""
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for i in range(stringLength))


class ChartConfig(NamedTuple):
    width: int
    height: int
    title: str = ""
    labels: List = []  # Legend labels
    colors: List = []
    bg_color: str = "#ffffff"
    link: str = None
    series_labels: List = []  # for Bar, StackedBar and Line
    data_labels: List = (
        []
    )  # Labels for in the chart itself. Currently only implemented for StackedBarChart
    max_x_axis: float = None  # Currently only for StackedBarChart and ScatterChart
    min_x_axis: float = None  # Currently only for ScatterChart
    max_y_axis: float = None  # Currently only for StackedBarChart and ScatterChart
    min_y_axis: float = None  # Currently only for ScatterChart
    horizontal: bool = False  # Currently only for StackedBarChart
    x_type: str = "float"  # Currently only for ScatterChart
    x_axis_max_ticks: int = 0
    x_axis_font_size: int = 0
    y_axis_max_ticks: int = 0
    y_axis_step_size: int = 0
    y_axis_font_size: int = 0
    y_axes_placement: list = [
        "left"
    ]  # For each series either the left or the right y_axes is used
    tension: float = 0  # How smooth the (line) chart is 1 is very (extremely) smooth
    padding: int = 40  # distance to next object
    show_legend: bool = True  # Set to False to hide legend in pie charts or line charts
    css_class: str = ""


class Chart(Block):
    def __init__(self, values, config):
        id = id_pattern.sub("", config.title) + "_" + randomString()
        # padding = config.padding if hasattr(config,'padding') else None
        super().__init__(
            block_id=id,
            width=config.width,
            height=config.height,
            bg_color=config.bg_color,
            link=config.link,
            padding=config.padding,
            css_class=config.css_class,
        )

        self.datasets = f"""[{{
                    data: {str(values)},
                    backgroundColor: {str(config.colors)},
                    label: 'abc'
                }}]"""
        self.values = values
        self.config = config
        self.labels = config.labels  # Can be overwritten
        self.canvas_height_difference = (
            150  # Difference between div height and canvas height, can be overwritten
        )
        self.xmin = (
            "min: 0,"
            if config.min_x_axis == None
            else f'min: "{config.min_x_axis}",'
            if isinstance(config.min_x_axis, str)
            else f"suggestedMin: {config.min_x_axis},"
        )
        self.xmax = (
            ""
            if config.max_x_axis == None
            else f'max: "{config.max_x_axis}",'
            if isinstance(config.max_x_axis, str)
            else f"max: {config.max_x_axis},"
        )
        self.x_axis_max_ticks = (
            f"maxTicksLimit: {config.x_axis_max_ticks},"
            if config.x_axis_max_ticks
            else ""
        )
        self.x_axis_font_size = f"font: {{size: {config.x_axis_font_size if config.x_axis_font_size else 9} }},"
        self.ymin = (
            "min: 0,"
            if config.min_y_axis == None
            else f"suggestedMin: {config.min_y_axis},"
        )
        self.ymax = "" if config.max_y_axis == None else f"max: {config.max_y_axis},"
        self.y_axis_step_size = (
            f"stepSize: {config.y_axis_step_size}," if config.y_axis_step_size else ""
        )
        self.y_axis_max_ticks = (
            f"maxTicksLimit: {config.y_axis_max_ticks},"
            if config.y_axis_max_ticks and not config.y_axis_step_size
            else ""
        )
        self.y_axis_font_size = f"font: {{size: {config.y_axis_font_size if config.y_axis_font_size else 9} }},"

    def do_render(self, position: str, options: dict):
        data = f"""{{
                datasets: {self.datasets},
                labels: {str(self.labels)}
            }}"""

        return f"""<div style="position:{position}; left:{options['left']}px; top:{options['top']}px; width:{self.width}px; height:{self.height}px; background-color:{self.bg_color}; margin-bottom:{self.padding}">
		        <canvas id="{self.block_id}_canvas" width="{self.width}px" height="{self.height - self.canvas_height_difference}px"></canvas>
            </div>
        
            <script>
                //Chart.plugins.unregister(ChartDataLabels); // To make sure not all charts show labels automatically
                window.addEventListener('load',  function() {{
                    var ctx_{self.block_id} = document.getElementById('{self.block_id}_canvas').getContext('2d');
                    window.{self.block_id}Chart = new Chart(ctx_{self.block_id}, {{
                        type: '{self.type}', 
                        data: {data}, 
                        //plugins: [ChartDataLabels], // Add this line to enable data labels for this chart
                        options: {self.options}
                    }});
                }})
        
            </script>"""

    def render(self, align=""):
        options = {"left": 0, "top": 0}
        return self.do_render("relative", options)

    def render_absolute(self, left, top):
        options = {"left": left, "top": top}
        return self.do_render("absolute", options)


class PieChart(Chart):
    def __init__(self, values, config):
        super().__init__(values, config)

        self.type = "doughnut"
        self.options = f"""{{
                responsive: true,
                plugins: {{
                    legend: {{
                        position: 'top',
                        display: '{str(config.show_legend).lower()}'
                    }},
                }},
                title: {{
                    display: false
                }},
                animation: {{
                    animateScale: true,
                    animateRotate: true
                }},
                cutoutPercentage: 30
        }}"""


class BarChart(Chart):
    def __init__(self, values, config):
        super().__init__(values, config)

        self.type = "bar"
        # colors = config.colors if len(config.colors) == 1 else config.colors * len(values)

        colors = (
            config.colors * len(values) if len(config.colors) == 1 else config.colors
        )
        # self.datasets = '['
        # for label, value, color in zip(config.series_labels, values, config.colors):
        self.datasets = f"""[{{
                                label: "",
                                data: {values},
                                backgroundColor: {colors}
                              }}]"""
        # self.datasets = self.datasets[:-1] + ']'
        self.labels = config.series_labels
        self.options = f"""{{
            indexAxis: "{'y' if config.horizontal else 'x'}",
            title: {{
                display: false
            }},
            plugins: {{
                legend: {{
                    display: false
                }}
            }},
            scales: {{
                x: {{
                     ticks: {{
                        {self.x_axis_max_ticks}
                        {self.x_axis_font_size}
                    }},
                    {self.xmin}
                    {self.xmax}
                    categoryPercentage: 0.9,
                    barPercentage: 0.9
                }},
                y: {{
                    ticks: {{
                        {self.y_axis_max_ticks}
                        {self.y_axis_step_size}
                        {self.y_axis_font_size}
                    }},
                    {self.ymin}
                    {self.ymax}
                }}      
            }}
        }}"""
        self.canvas_height_difference = 0

    def render(self, align=""):
        return super().render(align)

    def render_absolute(self, left, top):
        return super().render_absolute(left, top)


class StackedBarChart(Chart):
    """Creates a stacked bar chart with JSChart.
    values parameter is a list with one row of values per legend item.
    e.g.
    values = [[12000, 12500, 13000], # Salaries
              [800,800,800]]         # Housing
    chart_config = ChartConfig(
        width=300, height=200,
        colors=['#66cc66','#cc6666'],
        min_y_axis=0, max_y_axis=100, y_axis_max_ticks=10,
        labels=['Salaries', 'Housing'], series_labels=month_names)
    """

    def __init__(self, values, config):
        super().__init__(values, config)

        self.type = "bar"

        # Make datalabels as long as the rest, set a default and replace default where it was specified in data_labels param
        dl = ["{display: false }"] * len(values)
        for i, val in enumerate(config.data_labels):
            if val:
                dl[i] = val

        self.datasets = "["
        for label, value, color, dls in zip(
                config.labels, self.values, config.colors, dl
        ):
            if type(value) != type([]):
                # Single bar
                value = [value]
            self.datasets += f"""{{
                                    label: '{label}',
                                    data: {value},
                                    backgroundColor: '{color}',
                                    datalabels: {dls} 
                                  }},"""
        self.datasets = self.datasets[:-1] + "]"
        series_labels = config.series_labels if config.series_labels else [config.title]
        series_label_string = "', '".join([str(bl) for bl in series_labels])
        self.labels = f"['{series_label_string}']"
        ticks = f",ticks: {{max: {config.max_y_axis}}}" if config.max_y_axis else ""
        self.options = f"""{{
                indexAxis: "{'y' if config.horizontal else 'x'}",
                title: {{
                    display: false
                }},
            scales: {{
                x: {{
                   stacked: true,
                    ticks: {{
                        {self.x_axis_max_ticks}
                        {self.x_axis_font_size}
                    }},
                    {self.xmin}
                    {self.xmax}
                }},
                y: {{
                    stacked: true,
                    ticks: {{
                        {self.y_axis_max_ticks}
                        {self.y_axis_step_size}
                        {self.y_axis_font_size}
                    }},
                    {self.ymin}
                    {self.ymax}
                }}
            }}
        }}"""
        self.canvas_height_difference = 0  # Default is 150 but for bar charts the div doesn't need to be larger than the div


class LineChart(Chart):
    def __init__(self, values, config):
        super().__init__(values, config)

        self.type = "line"
        self.datasets = "["
        for label, value, color in zip(config.series_labels, values, config.colors):
            self.datasets += f"""{{
                                    yAxisID: '{label if label else "y"}',
                                    label: '{label}',
                                    data: {value},
                                    tension: {config.tension},
                                    pointRadius: 0,
                                    backgroundColor: '{color}', 
                                    borderColor: '{color}',
                                    borderWidth: 2,
                                    fill: false, 
                                  }},"""
        self.datasets = self.datasets[:-1] + "]"

        y_axes_placement = config.y_axes_placement + ["left"] * (
                len(values) - len(config.y_axes_placement)
        )
        # y_axes_config = "[" if len(config.series_labels) > 1 else ""
        y_axes_config = ""
        for index, label in enumerate(config.series_labels):
            # Vreemd, komt het voor dat deze loop meer dan 1x doorlopen wordt? Dan zou er toch [] omheen moeten
            y_axes_config += f"""
                {label if label else 'y'}: {{
                    type: 'linear',
                    position: '{y_axes_placement[index]}',
                    min: 0,
                    ticks: {{
                        {self.y_axis_max_ticks}
                        {self.y_axis_step_size}
                        {self.y_axis_font_size}
                    }},
                    {self.ymin}
                    {self.ymax}
                }},"""
        y_axes_config = y_axes_config[:-1]
        # if len(config.series_labels) > 1:
        #    y_axes_config += "]"

        self.options = f"""{{
            title: {{
                display: false
            }},
            plugins: {{
                legend: {{
                    position: 'top',
                    display: {str(config.show_legend).lower()}
                }},
            }},
            scales: {{
                x: {{
                    ticks: {{
                        {self.x_axis_max_ticks}
                        {self.x_axis_font_size}
                    }},
                    {self.xmin}
                    {self.xmax}
                    categoryPercentage: 0.9,
                    barPercentage: 0.9
                }},
                {y_axes_config}
            }}
        }}"""


BORDER_COLOR = 0
FILL_COLOR = 1


class ScatterChart(Chart):
    def __init__(self, values, config):
        super().__init__(values, config)

        self.type = "line"
        self.datasets = "["
        if config.x_type == "date":
            valuestr = "["
            for v in values:
                valuestr += f"{{ 'x':'{v['x']}', 'y': {v['y']} }}, "
            valuestr = valuestr[:-2] + "]"
        else:
            valuestr = values
        self.datasets += f"""{{
                                label: '{config.title}',
                                data: {valuestr},
                                borderColor: '{config.colors[BORDER_COLOR]}',
                                backgroundColor: '{config.colors[FILL_COLOR]}',
                                borderWidth: 1,
                                tension: {config.tension}, 
                                fill: true, 
                              }},"""
        self.datasets = self.datasets[:-1] + "]"
        # self.labels = []
        self.canvas_height_difference = (
            0  # Is for scatter chart other than for other chart types
        )

        self.options = f"""{{
            title: {{
                display: false
            }},
            plugins: {{
                legend: {{
                    display: false
                }}
            }},
            elements: {{
                point:{{
                    radius: 0
                }}
            }},
            scales: {{
                x: {{
                    position: 'bottom',
                    type: 'time',
                    time: {{
                        {self.x_axis_max_ticks}
                        {self.x_axis_font_size}
                        {self.xmin}
                        {self.xmax}
                        unitStepSize: 1
					}},
                    ticks: {{
                        font: {{size: 9}}
                    }},
					scaleLabel: {{
						display: true
					}},
                    gridLines: {{
                        offsetGridLines: false
                    }}
                }},      
                y: {{
                    ticks: {{
                        {self.y_axis_max_ticks}
                        {self.y_axis_step_size}
                        {self.y_axis_font_size}
                    }},
                    {self.ymin}
                    {self.ymax}
            }}    
            }}
        }}"""


class MultiScatterChart(Chart):
    def __init__(self, value_lists, config):
        # value_lists is the list of data lines. Each line is a list of values.
        super().__init__(value_lists, config)

        self.type = "line"
        self.datasets = "["
        for i, values in enumerate(value_lists):
            if config.x_type == "date":
                valuestr = "["
                for v in values:
                    valuestr += f"{{ 'x':'{v['x']}', 'y': {v['y']} }}, "
                valuestr = valuestr[:-2] + "]"
            else:
                valuestr = values
            self.datasets += f"""{{
                                    label: '{config.title}',
                                    data: {valuestr},
                                    borderColor: '{config.colors[i][BORDER_COLOR]}',
                                    backgroundColor: '{config.colors[i][FILL_COLOR]}',
                                    borderWidth: 1, 
                                    fill: true, 
                                    tension: {config.tension}
                                  }},"""
        self.datasets = self.datasets[:-1] + "]"
        # self.labels = []
        self.canvas_height_difference = (
            0  # Is for scatter chart other than for other chart types
        )

        self.options = f"""{{
            title: {{
                display: false
            }},
            plugins: {{
                legend: {{
                    display: false
                }}
            }},
            elements: {{
                point:{{
                    radius: 0
                }}
            }},
            scales: {{
                x: {{
                    position: 'bottom',
                    type: 'time',
                    time: {{
                        {self.x_axis_max_ticks}
                        {self.x_axis_font_size}
                        {self.xmin}
                        {self.xmax}
                        unitStepSize: 1
					}},
                    ticks: {{
                        font: {{size: 9}}
                    }},
					scaleLabel: {{
						display: true
					}},
                    gridLines: {{
                        offsetGridLines: false
                    }}
                }},      
                y: {{
                    ticks: {{
                        {self.y_axis_max_ticks}
                        {self.y_axis_step_size}
                        {self.y_axis_font_size}
                    }},
                    {self.ymin}
                    {self.ymax}
                }}     
            }}
        }}"""


# class Option():
#     def __init__(self, name, contents=None):
#         self.name = name
#         self.contents = contents
#
#     def render(self, chart):
#         if not self.contents:
#             if hasattr( chart, self.name ):
#                 return self.name + ':' + self.str(getattr( chart, self.name ))
#             else:
#                 return ''
#         else:
#             contents = [option.render(chart) for option in self.contents]
#             content_string =  ','.join([c for c in contents if c])
#             name_qualifier = self.name + ':' if self.name else ''
#             return name_qualifier + '{' + content_string + '}'
#
#     def str(self, value):
#         if isinstance(value, bool):
#             return str(value).lower()
#         else:
#             return str(value)
#
# class Test():
#     def __init__(self):
#         self.display = False
#         self.radius = 3
#
# if __name__=='__main__':
#
#     chart = Test()
#
#     structure = Option( '', [
#             Option( 'legend', [
#                 Option( 'display' ),
#                 Option( 'size' )
#                 ]),
#             Option( 'elements', [
#                 Option( 'point', [
#                     Option('radius')
#                 ])
#             ])
#         ])
#
#     print( structure.render( chart ) )
