/* = JOB STUFF ============================================================== */
!function ($) {
    "use strict"; // jshint ;_;

    $('#add_multifile').click( function(){
	$('#multifilelist').append('<input class="multifileitem" type="text"></input>');
    });

    $('#jobstart').click( function(){

	var multifiles = [];
	$("input.multifileitem").each(function(){
	    var str = $(this).val();
	    if( str.length > 0 ){
		multifiles.push( $(this).val() );
	    }
	});
	
        var xhr = new XMLHttpRequest();

        xhr.onreadystatechange = function( e ){
            if( 4 == this.readyState ){
                alert( "job sended" );
                refreshJobList();
            }
        };

        xhr.open( 'POST', '/web/ajax/job', true );
	
        var form = $('#jobform')[0];
        var fd = new FormData( form );
	fd.append( 'multifiles', multifiles );
        xhr.send( fd );
    });

    refreshJobList();

}(window.jQuery);

function refreshJobList(){
    $.ajax({
        dataType: "json",
        url: '/web/ajax/job',
        success: function( data ) {
            var items = [];
            var jobs = data['jobs']

            $.each( jobs, function( key, val ) {
                items.push('<li><a href="/web/job/' + val['id'] + '">Job ' + val['id'] + '</a></li>');
            });

            var newlist = $('<ul/>', {
                'id': 'joblist',
                'class': 'unstyled',
                html: items.join('')
            });

            $('#joblist').replaceWith( newlist );
        }
    });
}
