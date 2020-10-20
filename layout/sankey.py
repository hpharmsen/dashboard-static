import json
import os
from layout.block import Page, Block
from layout.chart import id_pattern, randomString, ChartConfig


class SankeyChart(Block):
    def __init__(self, values, config, limited=False):
        id = id_pattern.sub('', config.title) + '_' + randomString()
        super().__init__(
            id=id, width=config.width, height=config.height, bg_color=config.bg_color, link=config.link, limited=limited
        )
        self.canvas_height_difference = 150  # Difference between div height and canvas height, can be overwritten
        self.values = values

    def do_render(self, left, top, position):

        values_json = json.dumps( self.values )
        return f'''
            <!-- Add style to links or they won't appear properly-->
            <style>
                .link {{
                  fill: none;
                  stroke: #000;
                  stroke-opacity: .2;
                }}
                .link:hover {{
                  stroke-opacity: .5;
                }}
            </style>
            
            <div id="{self.id}" style="position:{position}; left:{left}px; top:{top}px; width:{self.width}px; height:{self.height}px; background-color:{self.bg_color}">
		        <canvas width="{self.width}px" height="{self.height - self.canvas_height_difference}px"></canvas>
            </div>

            <script>

                // set the dimensions and margins of the graph
                var margin = {{top: 10, right: 10, bottom: 10, left: 10}},
                    width = 450 - margin.left - margin.right,
                    height = 480 - margin.top - margin.bottom;
                
                // append the svg object to the body of the page
                var svg = d3.select("#{self.id}").append("svg")
                    .attr("width", width + margin.left + margin.right)
                    .attr("height", height + margin.top + margin.bottom)
                    .append("g")
                    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");
                
                // Color scale used
                var color = d3.scaleOrdinal(d3.schemeCategory20);
                
                // Set the sankey diagram properties
                var sankey = d3.sankey()
                    .nodeWidth(36)
                    .nodePadding(290)
                    .size([width, height]);
                    
                var graph = {values_json};
                
                
                  // Constructs a new Sankey generator with the default settings.
                  sankey
                      .nodes(graph.nodes)
                      .links(graph.links)
                      .layout(1);
                
                  // add in the links
                  var link = svg.append("g")
                    .selectAll(".link")
                    .data(graph.links)
                    .enter()
                    .append("path")
                      .attr("class", "link")
                      .attr("d", sankey.link() )
                      .style("stroke-width", function(d) {{ return Math.max(1, d.dy); }})
                      //.sort(function(a, b) {{ return b.dy - a.dy; }});
                
                  // add in the nodes
                  var node = svg.append("g")
                    .selectAll(".node")
                    .data(graph.nodes)
                    .enter().append("g")
                      .attr("class", "node")
                      .attr("transform", function(d) {{ return "translate(" + d.x + "," + d.y + ")"; }})
                      .call(d3.drag()
                        .subject(function(d) {{ return d; }})
                        .on("start", function() {{ this.parentNode.appendChild(this); }})
                        .on("drag", dragmove));
                
                  // add the rectangles for the nodes
                  node
                    .append("rect")
                      .attr("height", function(d) {{ return d.dy; }})
                      .attr("width", sankey.nodeWidth())
                      .style("fill", function(d) {{ return d.color = color(d.name.replace(/ .*/, "")); }})
                      .style("stroke", function(d) {{ return d3.rgb(d.color).darker(2); }})
                    // Add hover text
                    .append("title")
                    .text(function(d) {{ return d.name + " " + "There is " + d.value + " stuff in this node"; }});
                
                  // add in the title for the nodes
                    node
                        .append("text")
                        .attr("x", -6)
                        .attr("y", function(d) {{ return d.dy / 2; }})
                        .attr("dy", ".35em")
                        .attr("text-anchor", "end")
                        .attr("transform", null)
                        .text(function(d) {{ return d.name; }})
                        .filter(function(d) {{ return d.x < width / 2; }})
                        .attr("x", 6 + sankey.nodeWidth())
                        .attr("text-anchor", "start");
                
                  // the function for moving the nodes
                  function dragmove(d) {{
                    d3.select(this)
                      .attr("transform",
                            "translate("
                               + d.x + ","
                               + (d.y = Math.max(
                                  0, Math.min(height - d.dy, d3.event.y))
                                 ) + ")");
                    sankey.relayout();
                    link.attr("d", sankey.link() );
                  }}
            </script>'''

    def render(self, align='', limited=False):
        if self.limited and limited:
            return ''
        return self.do_render(0, 0, 'relative')

    def render_absolute(self, left, top, limited=False):
        if self.limited and limited:
            return ''
        return self.do_render(left, top, 'absolute')


if __name__ == '__main__':

    costs = [
        ('Management', 103),
        ('Medewerkers', 518),
        ('Huisvesting', 30),
        ('Afschrijvingen', 8),
        ('Marketing', 38),
        ('Overige kosten', 99)]

    turnovers = [
        ('Accell IT', 386096),
        ('T-Mobile', 171362),
        ('TOR groep', 159400),
        ('BAM', 145540),
        ('Trustmarketing', 141005),
        ('Atos', 117680),
        ('Volksbank', 39082),
        ('Oerol', 25924),
        ('IDFA', 24272),
        ('NuTestament', 24218),
        ('TMC', 14656),
        ('Oncode', 12737),
        ('VVV Terschelling', 7495),
        ('Tommy', 7330),
        ('De Boer', 7330),
        ('VVV Texel', 6900),
        ('AMS-IX', 6390),
        ('AssistiveWare', 5872),
        ('Thales', 5595),
        ('VVV Ameland', 5590),
        ('Van Esch', 3308),
        ('Kuehne+Nagel', 2880),
        ('BeleefRoutes', 1962),
        ('Stichting van het Kind', 1705),
        ('Houthoff', 1700),
        ('De Breij', 1578),
        ('Ajax', 1489),
        ('Avero', 1471),
        ('IVA driebergen', 1380),
        ('Kpito', 1380),
        ('KCP', 1354),
        ('IMC', 1278),
        ('Tennet', 1265),
        ('Ortec', 1200),
        ('TOPA', 1160),
        ('Saton', 1035),
        ('Qikker', 878),
        ('Functionals', 858),
        ('VVV Schiermonnikoog', 600),
        ('Zoetermeer', 420),
        ('Apple', 221),
        ('Metroprop', 150)]
    turnovers = [(name, int(round(turnover / 1000, 0))) for name, turnover in turnovers if turnover > 1500]

    tot_costs = sum([c[1] for c in costs])
    tot_turnover = sum([t[1] for t in turnovers])
    profit = tot_turnover - tot_costs
    if profit > 0:
        costs += [('profit', profit)]
    print(tot_turnover, tot_costs, profit)

    sankey_data = {
"nodes":[
{"node":0,"name":"node0"},
{"node":1,"name":"node1"},
{"node":2,"name":"node2"},
{"node":3,"name":"node3"},
{"node":4,"name":"node4"},
{"node": 5, "name": "node5"}
],
"links":[
{"source":0,"target":3,"value":2},
{"source":1,"target":3,"value":2},
{"source": 2, "target": 3, "value": 2},
{"source":3,"target":4,"value":2},
{"source":3,"target":5,"value":2}]}


    os.chdir('..')
    chart = SankeyChart(
        sankey_data,
        ChartConfig(
            width=800,
            height=600
        ))
    page = Page([chart])

    page.render('output/sankey.html')
    #page.render('output/limited/sales.html', limited=1)
