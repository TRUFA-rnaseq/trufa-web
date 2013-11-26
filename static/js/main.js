/* = DEBUG ==================================================================== */
function showWarning( msg ){
    if( $('#msgerror').length ){
        $('#msgerror').append( '<div class="alert">' + msg + '</div>' );
    }
}

function showError( msg ){
    if( $('#msgerror').length ){
        $('#msgerror').append( '<div class="alert alert-error">' + msg + '</div>' );
    }
}

/* = USER NAME = ============================================================== */
!function ($) {
    "use strict"; // jshint ;_;

    if( $( '#username').length ){
        refreshUserName();
    }

}(window.jQuery);

function getUserName( f_ok ){
    $.ajax({
        dataType: "json",
        url: '/ajax/me',
        success: function( data ) { f_ok( data['username'] ) }
    });
}

function refreshUserName(){
    getUserName( function( username ){
        $('#username').replaceWith( '<p>' + username + '</p>' );
    });
}

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
        var input = document.getElementById('filesel')
        var size = getFileSize( input )
        if( size > 0 && size < 2*1024*1024*1024 ){
            sendLittleFile()
        }else{
            sendBigFile()
        }
    });

}(window.jQuery);

function getFileSize( input ){
    if( ! window.FileReader) {
        showError( "The file API isn't supported on this browser yet." );
    }else if( ! input ){
        showError( "Couldn't find the file input element." );
    }else if( ! input.files ){
        showError( "This browser doesn't support the `files` property of file inputs.");
    }else if( ! input.files[0] ){
        showError( "Please select a file before clicking 'Load'" );
    }else{
        var file = input.files[0];
        return file.size;
    }

    return 0;
}

function sendLittleFile(){
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
}

function sendBigFile(){
    showError( "Can't load Files > 2 GBs" )
    // var input = $('#filesel')[0]
    // var file = input.files[0]
    // showWarning( file )
    // var blob = file.slice( 0, 1024 )
    // showWarning( file + " size" + blob.size )
}

/* = FILE LIST ============================================================== */
!function ($) {
    "use strict"; // jshint ;_;

    refreshFileList();

}(window.jQuery);

function getFileList( f_ok ){
    $.ajax({
        dataType: "json",
        url: '/ajax/file',
        success: function( data ) { f_ok( data['files'] ) }
    });
}

function getFileListWithType( ftype, f_ok ){
    var tname = typeof ftype
    if( tname == "number" ){
        $.ajax({
            dataType: "json",
            data: { filetype: ftype },
            url: '/ajax/file',
            success: function( data ) { f_ok( data['files'] ) }
        });
        return
    }else if( tname == "object" ){
        if( ftype.constructor == Array ){
            getFileListWithTypes_([], ftype, f_ok )
            return
        }
    }
    showError( "unknown file type" )
}

function getFileListWithTypes_( items, ftype, f_ok ){
    if( ftype.length == 0 ){
        f_ok( items )
    }else{
        var xs = ftype.slice(1)
        $.ajax({
            dataType: "json",
            data: { filetype: ftype[0] },
            url: '/ajax/file',
            success: function( data ) {
                $.each( data['files'], function(key, val){
                    items.push( val )
                });
                getFileListWithTypes_( items, xs, f_ok )
            }
        });
    }
}

function refreshFileList(){
//    var in_type = $("input[name=input_type]")

//    if var in_type == "single" 

    var items1 = [];
    var items2 = [];
    var items3 = [];

// Getting all files for list in the home page
    getFileList( function( files ){
	$.each(files, function(key, val){
            items1.push('<li>' + val['file'] + '</li>');
	});
        var newlist = $('<ul/>', {
            'id': 'filelist',
            'class': 'unstyled',
            html: items1.join('')
        });
        $('#filelist').replaceWith( newlist );

    });

// Getting only reads files for the "start a job" form
    getFileListWithType( 1,  function( files ){

        $.each(files, function( key, val ) {
            items2.push('<option value="' + val['id'] + '">' + val['file'] + '</option>');
        });

        var newformlist = $('<select/>', {
            'id': 'jobfile',
            'name': 'file',
            html: items2.join('')
        });

        $('#jobfile').replaceWith( newformlist );
// EK edit --------------------------------------------------
         var newformlist = $('<select/>', {
            'id': 'jobfile2',
            'name': 'file2',
             html: items2.join('')
        });

        $('#jobfile2').replaceWith( newformlist );
    });

// Getting only assembly files for the "start a job" form
    getFileListWithType( 4,  function( files ){

        $.each(files, function( key, val ) {
            items3.push('<option value="' + val['id'] + '">' + val['file'] + '</option>');
        });

         var newformlist = $('<select/>', {
            'id': 'jobfile3',
            'name': 'file3',
             html: items3.join('')
        });

        $('#jobfile3').replaceWith( newformlist );


        // var newformlist = $('<select/>', {
        //     'id': 'jobfile3',
        //     'name': 'file',
        //     html: items2.join('')
        // });

        // $('#jobfile3').replaceWith( newformlist );

// EK edit --------------------------------------------------
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
    //  e.preventDefault();
    //  $(this).tab('show');
    // })

// Select the number and type of input:

$(document).ready(function(){
    var reads_1 = $("div[id=reads_1]")
    var reads_2 = $("div[id=reads_2]")
    var assembly_in = $("div[id=assembly_in]")
    var in_type = $("input[name=input_type]")

// Setting single or paired reads
    in_type.change(function (){
        var in_type = $("input[name=input_type]:checked").val()
	$('#demo').append(in_type)

	switch(in_type){
	case "single": 
            reads_1.children("label").text("Single reads file:")
            reads_1.show()
            reads_2.hide()
	    assembly_in.hide()
	    break;
	case "paired":
            reads_1.children("label").text("Left reads file:")
            reads_1.show()
            reads_2.show()
	    assembly_in.hide()
	    break;
	case "contigs":
            reads_1.hide()
            reads_2.hide()
	    assembly_in.show()
	    break;
	case "contigs_with_single":
            reads_1.children("label").text("Single reads file:")
	    reads_1.show()
	    assembly_in.show()
            reads_2.hide()
	    break;
	case "contigs_with_paired":
	    reads_1.children("label").text("Left reads file:")
	    reads_1.show()
            reads_2.show()
	    assembly_in.show()
	    break;
	}
    });
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
