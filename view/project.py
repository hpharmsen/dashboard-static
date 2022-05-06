import os
from pathlib import Path

from layout.basic_layout import HEADER_SIZE, MID_SIZE
from layout.block import TextBlock, Page, VBlock, HBlock
from settings import get_output_folder

# options.url = "http://cors.corsproxy.io/url=" + options.url;
JAVASCRIPT = """
    $.ajaxPrefilter( function (options) {
        if (options.crossDomain && jQuery.support.cors) {
            var http = (window.location.protocol === 'http:' ? 'http:' : 'https:');
            options.url = http + '//cors-anywhere.herokuapp.com/' + options.url;
        }
    });
    
    function do_load() {
        let searchParams = new URLSearchParams(window.location.search)
        if (searchParams.has('project')) {
            var project_url = "https://oberon-dashboard-api.herokuapp.com/project/" + searchParams.get('project');
            
            $.getJSON(project_url, function(data) {
                $("#project_name > span").html(data.organization + " - " + data.project_name);
                $("#from_date > span").html(data.from_date);
                $("#until_date > span").html(data.until_date);
                $("#pm > span").html(data.pm);
                
                $("#client_hours > span").html(data.client_hours);
                $("#billable_hours > span").html(data.billable_hours);
                $("#writeoffs > span").html(data.writeoffs);
                //$("#hourly_rate > span").html(data.hourly_rate);

                $("#team_grid > span").html("");
                table = document.createElement("table")
                data.team.forEach((line) => {
                    row = document.createElement("tr");
                    cell1 = document.createElement("td");
                    cell1.textContent = line["employee"]
                    cell2 = document.createElement("td");
                    cell2.textContent = line["hours"]
                    row.append(cell1, cell2);
                    table.append(row);
                });
                $("#team_grid > span").append(table)
            });
        }
    }
    
    $(window).on('hashchange', function(e){
        do_load();
    });
    
    do_load()
"""


def render_project_page(output_folder: Path):
    grid = HBlock(
        [
            VBlock(
                [
                    TextBlock("Omzet"),
                    TextBlock("Inkoop"),
                    TextBlock("Marge"),
                    TextBlock(""),
                    TextBlock("Klanturen"),
                    TextBlock("Billable uren"),
                    TextBlock("Afschrijvingen"),
                    TextBlock("Gem. uurloon"),
                ]
            ),
            VBlock(
                [
                    TextBlock("-", 16, block_id="turnover"),
                    TextBlock("-", 16, block_id="costs"),
                    TextBlock("-", 16, block_id="margin"),
                    TextBlock(""),
                    TextBlock("-", 16, block_id="client_hours"),
                    TextBlock("-", 16, block_id="billable_hours"),
                    TextBlock("-", 16, block_id="writeoffs"),
                    TextBlock("-", 16, block_id="hourly_rate"),
                ]
            ),
        ]
    )

    page = Page(
        [
            TextBlock(
                "organization - project_name", HEADER_SIZE, block_id="project_name"
            ),
            HBlock(
                [
                    TextBlock("Van", color="gray"),
                    TextBlock("-", 20, block_id="from_date"),
                    TextBlock("tot", color="gray"),
                    TextBlock("-", 20, block_id="until_date"),
                ]
            ),
            HBlock([TextBlock("PM", color="gray"), TextBlock("-", 20, block_id="pm")]),
            TextBlock(""),
            HBlock(
                [
                    VBlock([TextBlock("KPI's", MID_SIZE), grid]),
                    VBlock(
                        [
                            TextBlock("Team", MID_SIZE),
                            TextBlock("team_grid", block_id="team_grid", color="gray"),
                        ]
                    ),
                ]
            ),
        ]
    )

    page.add_onloadcode(JAVASCRIPT)
    page.render(output_folder / "project.html")


if __name__ == "__main__":
    os.chdir("..")

    render_project_page(get_output_folder())
