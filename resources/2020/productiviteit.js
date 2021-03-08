// Hide the results per user, we only show one at a time
function hide_user_blocks() {
    var userblocks = document.querySelectorAll('*[id^="productiviteit_"]');
    for (var i=0;i < userblocks.length;i++) {
         userblocks[i].style.display = "none";
    }
}

function make_users_clickable() {

	hide_user_blocks();
	var index = 0
    $("#overzicht table tr").each( function() { // td:first-child
        if (index!=0) {
            //alert( $(this).html() )
            var user = $(this).find("span:first").html();
            //alert( user )
            $(this).hover( function() {
                $(this).css('cursor','pointer');
                hide_user_blocks();
                $('#productiviteit_'+user).show();
            });
            $(this).click( function() {
                window.location.href = 'productiviteit_' + user + '.html';
            });
        }
        index +=1;
    });
};
