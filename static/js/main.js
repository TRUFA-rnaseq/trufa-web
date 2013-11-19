/* = FILE UPLOAD ============================================================== */
!function ($) {
    "use strict"; // jshint ;_;

    var filesel = $('input[id=filesel]');
    filesel.change( function(){
        $('#filename').val( $(this).val() );
    });
    filesel.css( 'position', 'absolute' );
    filesel.css( 'visibility', 'hidden' );

    $('#filealert').css( 'visibility', 'hidden' );

    $('#filebrowse').click( function(){
        $('#filesel').click();
    });

    $('#filesend').click( function(){
        $('#filebar > .bar').replaceWith( '<div class="bar" style="width: 0%;"></div>' );
        $('#filebar').addClass( 'progress-striped' );
        $('#filebar').addClass( 'active' );
        $('#filealert').css( 'visibility', 'hidden' );
        var xhr = new XMLHttpRequest();
        if( xhr.upload ){
            xhr.upload.onprogress = function( e ){
                var done = e.position || e.loaded, total = e.totalSize || e.total;
                var perc = (Math.floor(done/total*1000)/10);
                $('#filebar > .bar').css( 'width', perc + '%' );
            };
        }
        xhr.onreadystatechange = function( e ){
            if( 4 == this.readyState ){
                $('#filebar > .bar').css( 'width', '100%' );
                $('#filebar').removeClass( 'progress-striped' );
                $('#filebar').removeClass( 'active' )
                $('#fileform').css( 'visibility', 'visible' );
                $('#filealert').css( 'visibility', 'visible' );
                refreshFileList();
            }
        };

        xhr.open( 'PUT', '/ajax/file', true );

        var form = $('#fileform')[0];
        var fd = new FormData( form );
        xhr.send( fd );

        $('#fileform').css( 'visibility', 'hidden' );
    });

}(window.jQuery);

/* = FILE LIST ============================================================== */
!function ($) {
    "use strict"; // jshint ;_;

    refreshFileList();

}(window.jQuery);

function refreshFileList(){
    $.ajax({
        dataType: "json",
        url: '/ajax/file',
        success: function( data ) {
            var items1 = [];
            var items2 = [];
            var files = data['files']

            $.each(files, function( key, val ) {
                items1.push('<li>' + val['file'] + '</li>');
                items2.push('<option value="' + val['id'] + '">' + val['file'] + '</option>');
            });

            var newlist = $('<ul/>', {
                'id': 'filelist',
                'class': 'unstyled',
                html: items1.join('')
            });

            $('#filelist').replaceWith( newlist );

            var newformlist = $('<select/>', {
                'id': 'jobfile',
                'name': 'file',
                html: items2.join('')
            });

            $('#jobfile').replaceWith( newformlist );
// EK edit --------------------------------------------------
            // var newformlist = $('<select/>', {
            //     'id': 'jobfile2',
            //     'name': 'file2',
            //     html: items2.join('')
            // });

            // $('#jobfile2').replaceWith( newformlist );

            // var newformlist = $('<select/>', {
            //     'id': 'jobfile3',
            //     'name': 'file',
            //     html: items2.join('')
            // });

            // $('#jobfile3').replaceWith( newformlist );

// EK edit --------------------------------------------------


        }
    });
}

/* = JOB STUFF ============================================================== */
!function ($) {
    "use strict"; // jshint ;_;

    $('#jobstart').click( function(){
        var xhr = new XMLHttpRequest();

        xhr.onreadystatechange = function( e ){
            if( 4 == this.readyState ){
                alert( "job sended" );
                refreshJobList();
            }
        };

        xhr.open( 'POST', '/ajax/job', true );
	
        var form = $('#jobform')[0];
        var fd = new FormData( form );
        xhr.send( fd );
    });

    refreshJobList();

}(window.jQuery);

function refreshJobList(){
    $.ajax({
        dataType: "json",
        url: '/ajax/job',
        success: function( data ) {
            var items = [];
            var jobs = data['jobs']

            $.each( jobs, function( key, val ) {
                items.push('<li><a href="/job/' + val['id'] + '">Job ' + val['id'] + '</a></li>');
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

/*EK EDITS =================================================================== */

    <!-- to prevent the screen to move when user click on a tab -->
    $('.nav-tabs').click(function (e) {
	e.preventDefault();
    });


    <!-- Scroll down when clicking on the accordion -->
    $('.accordion-toggle').click(function (e) {
	e.preventDefault();
	var n = $(document).height();
	$('html, body').animate({ scrollTop: n/2 },'500');
    });

    // <!-- Enable tabs -->
    // $('#myTab a').click(function (e) {
    // 	e.preventDefault();
    // 	$(this).tab('show');
    // })

// Select the number and type of input:

$(document).ready(function(){
    var reads_1 = $("div[id=reads_1]")
    var reads_2 = $("div[id=reads_2]")
    var in_type = $("input[name=input_type]")

// Setting single or paired reads
    in_type.change(function (){
	var in_type = $("input[name=input_type]:checked").val()

	if (in_type == "single")
	{
	    reads_1.children("label").text("Single reads file:")
	    reads_1.show()
	    reads_2.hide()
//	    $("p[id=demo]").text(in_type)
	}
	else if (in_type == "paired")
	{
	    reads_1.children("label").text("Left reads file:")
	    reads_1.show()
	    reads_2.show()
//	    $("p[id=demo]").text(in_type)
	}


    })
});
// Displaying warning message if action are not available with the current input
(function($) {
    var trin_check = $("input[id=trinity]")
    var warn = $('div[id=no_assembly_alert]')

    trin_check.change( function(){
	if (trin_check.is(':checked'))
	{
	    warn.hide()
	}
	else
	{
	    warn.show()
	}
    })
    
})(jQuery);


// Function to have activation/deactivation of checkboxes
$(function() {

    var in_type = $("input[name=input_type]")
    var warn_read = $('div[id=no_reads_alert]')

    in_type.change(function (){
	$("p[id=demo]").text($(this).val())

	cleaning_arr = ["single","paired","contigs_with_single","contigs_with_paired"]

	if (jQuery.inArray($(this).val(), cleaning_arr) === -1)
	{
	    $('.cleaning_steps').attr('disabled', true);
	    warn_read.show()
	}
	else
	{
	    $('.cleaning_steps').attr('disabled', false);
	    warn_read.hide()
	}
    });
});

$('#example').popover({html:true})

