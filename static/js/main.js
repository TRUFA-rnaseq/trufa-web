/* = DEBUG ==================================================================== */
function showClear( msg ){
    if( $('#msgerror').length ){
        $('#msgerror').empty()
    }
}

function showOK( msg ){
    if( $('#msgerror').length ){
        $('#msgerror').append( '<div class="alert alert-success">' + msg + '</div>' );
    }
}

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

function jumpTop(){
    $('html, body').animate( {scrollTop: '0px'}, 200 );
}

/* = USER NAME = ============================================================== */
!function ($) {
    "use strict"; // jshint ;_;

    if( $( '#navbar-username').length ){
        refreshNavbarUserName();
    }

}(window.jQuery);

function getUserName( f_ok ){
    $.ajax({
        dataType: "json",
        url: '/ajax/me',
        success: function( data ) { f_ok( data['username'] ) }
    });
}

function refreshNavbarUserName(){
    getUserName( function( username ){
        $('#navbar-username').html( username );
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
	 
	/* EK trial
	if( size >= 512*1024*1024 ){
            sendBigFile()
        }else if( size > 0 ){
            sendLittleFile()
        }
	*/
	if ( size <= 0 ){
	    showError( "No file has been uploaded")}
        else if( size < 512*1024*1024 ){
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
        showError( "Please select a file before clicking 'Upload'" );
    }else if($("#filetype").val() == "undef"){
	showError("The file type cannot be left to 'undefined'. Please specify the format of the input before clicking 'Upload'");
    }else{
        var file = input.files[0];
        return file.size;
    }

    return -1;
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

function sendBigFilePart( desc ){
    if( desc.sended >= desc.total ){
        sendBigFileEnd( desc )
    }else{
        var perc = Math.floor(desc.sended/desc.total*1000)/10
        $('#filebar > .bar').css( 'width', perc + '%' )

        var chunk = Math.min( desc.total - desc.sended, desc.chunkSize )
        var current = desc.sended
        var blob = desc.file.slice( current, current + chunk )

        desc.sended = desc.sended + chunk

        var xhr = new XMLHttpRequest();
        if( xhr.upload ){
            xhr.upload.onprogress = function( e ){
                var partdone = e.position || e.loaded
                var done = current + partdone
                var perc = Math.floor(done/desc.total*1000)/10
                $('#filealert').css( 'visibility', 'visible' );
                $('#filealert').html( "done " + done + " " + perc + "%" )
                $('#filebar > .bar').css( 'width', perc + '%' );
            };
        }
        xhr.onreadystatechange = function( e ){
            if( 4 == this.readyState ){
                sendBigFilePart( desc )
            }
        };

        xhr.open( 'PUT', '/ajax/filepart', true );

        var fd = new FormData();
        fd.append( 'myfile', blob )
        fd.append( 'status', 'part' )
        fd.append( 'myfilename', desc.filename )
        fd.append( 'myfiletype', desc.filetype )
        xhr.send( fd );
    }
}

function sendBigFileEnd( desc ){
    var xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function( e ){
        if( 4 == this.readyState ){
            $('#filebar > .bar').css( 'width', '100%' )
            $('#filebar').removeClass( 'progress-striped' )
            $('#filebar').removeClass( 'active' )
            $('#fileform').css( 'visibility', 'visible' )
            $('#filealert').css( 'visibility', 'visible' )
            $('#filealert').html( 'Upload Complete' )
            refreshFileList();
        }
    };

    xhr.open( 'PUT', '/ajax/filepart', true )

    var fd = new FormData()
    fd.append( 'status', 'end' )
    fd.append( 'myfilename', desc.filename )
    fd.append( 'myfiletype', desc.filetype )
    xhr.send( fd )
}

function sendBigFile(){
    $('#filebar > .bar').replaceWith( '<div class="bar" style="width: 0%;"></div>' );
    $('#filebar').addClass( 'progress-striped' );
    $('#filebar').addClass( 'active' );
    $('#filealert').css( 'visibility', 'hidden' );

    var input = $('#filesel')[0]
    var file = input.files[0]
    var descriptor = {
        sended: 0,
        file: file,
        filetype: $('#filetype').val(),
        filename: file.name,
        total: file.size,
        chunkSize: 5*1024*1024,
    }

    var xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function( e ){
        if( 4 == this.readyState ){
            sendBigFilePart( descriptor )
        }
    };

    xhr.open( 'PUT', '/ajax/filepart', true )

    var fd = new FormData()
    fd.append( 'status', 'start' )
    fd.append( 'myfilename', descriptor.filename )
    fd.append( 'myfiletype', descriptor.filetype )
    xhr.send( fd )

    $('#fileform').css( 'visibility', 'hidden' );
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
    getFileListWithType( [1,2],  function( files ){

        $.each(files, function( key, val ) {
            items2.push('<option value="' + val['id'] + '">' + val['file'] + '</option>');
        });

        var newformlist = $('<select>', {
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
    getFileListWithType( 5,  function( files ){

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

	    // Cancel Job if not correct input
	    if ( ! checkJobInput()){
	        return;
	    }

        xhr.onreadystatechange = function( e ){
            if( 4 == this.readyState ){
                var obj = $.parseJSON( this.responseText );
                if( ! obj.ok ){
                    alert( "Job ERROR: " + obj.msg );
                }else{
                    alert( "Job sent: Go to 'Home' to check its status" );
                }
            }
        };

        xhr.open( 'POST', '/ajax/job', true );

        var form = $('#jobform')[0];
        var fd = new FormData( form );
        xhr.send( fd );
    });

    refreshJobList();

}(window.jQuery);

function checkJobInput(){
    // if no input type is selected:
    if ( ! $("input[name=input_type]").is(':checked') ){
	alert("You have to select a type of input at the top of the page before submitting the job")
	return false
    }

    var in_type = $("input[name=input_type]:checked").val()
    // check input type: single
    if ( in_type == "single" ){
	if ( $('#jobfile').val() == null ) {
	    alert("You did not specify any reads file")
	    return false
	}	
    }
    // check input type: paired
    // if both reads files are the same:
    if ( in_type == "paired" ){
	if ( $('#jobfile').val() == null || $('#jobfile2').val() == null ){
	    alert("You did not specify two reads files")
	    return false
	}
    }
    // check input type: contigs
    if ( in_type == "contigs" ){
	if ( $('#jobfile3').val() == null ) {
	    alert("You did not specify any assembly file")
	    return false
	}	
    }
    // check input type: contigs_with_single:
    if ( in_type == "contigs_with_single" ){
	if ( $('#jobfile').val() == null ) {
	    alert("You did not specify any reads file")
	    return false
	}
	if ( $('#jobfile3').val() == null ) {
	    alert("You did not specify any assembly file")
	    return false
	}
    }
    // check input type: contigs_with_paired:
    if ( in_type == "contigs_with_paired" ){
	if ( $('#jobfile').val() == null || $('#jobfile2').val() == null ){
	    alert("You did not specify two reads files")
	    return false
	}
	if ( $('#jobfile3').val() == null ) {
	    alert("You did not specify any assembly file")
	    return false
	}
    }

    // if both reads files are the same:
    if ( in_type == "paired" || in_type == "contigs_with_paired"){
	if ( $('#jobfile').val() == $('#jobfile2').val()){
	    alert("You have to specify two different reads files as input")
	    return false
	}	
    }

    // if no analysis steps checked
    var steps = $(".cleaning_steps, .assembly_steps, .identification_steps, .mapping_steps, .expression_steps")

    if ( ! steps.is(":checked")){
	alert("You did not specify any analysis steps")
	return false
    }
    // if no adapters but cutadapt activated:
    if ($("#adapters").is(':checked')){
	if ($("#cutadapt_option1").val() == '' || $("#cutadapt_option2").val() == '' ){
	alert("You have selected Cutadapt but did not specify two adapter sequences: please input the sequences in Cutadapt options")
	}
	return false
    }
    return true
}

function refreshJobList(){
    $.ajax({
        dataType: "json",
        url: '/ajax/job',
        success: function( data ) {
            var items = [];
            var jobs = data['jobs']

            $.each( jobs, function( key, val ) {
                items.push('<li><a href="/job/' + val['id'] + '">Job ' + val['juid'] + '</a></li>');
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
// unchecking all boxes
	$('.cleaning_steps').attr('checked', false)
	$('.assembly_steps').attr('checked', false)
	$('.mapping_steps').attr('checked', false)
	$('.identification_steps').attr('checked', false)
	$('.expression_steps').attr('checked', false)

// No defaults for input files:
	document.getElementById("jobfile").selectedIndex = -1;
	document.getElementById("jobfile2").selectedIndex = -1;
	document.getElementById("jobfile3").selectedIndex = -1;

        var in_type = $("input[name=input_type]:checked").val()
//	$('#demo').append(in_type)
	var warn_read = $('div[id=no_reads_alert]')
	var warn_read2 = $('div[id=no_reads_alert2]')
	var warn_ass = $('div[id=no_assembly_alert]')


	switch(in_type){
	case "single": 
	    $('#jobfile').removeAttr('disabled')
	    $('#jobfile2').attr('disabled','disabled')
	    $('#jobfile3').attr('disabled','disabled')
            reads_1.children("label").text("Single reads file:")
            reads_1.show()
            reads_2.hide()
	    assembly_in.hide()
            $('.cleaning_steps').attr('disabled', false);
            $('.assembly_steps').attr('disabled', false);
	    warn_read.hide()
	    warn_read2.hide()
            $('.mapping_steps').attr('disabled', true);
            $('.identification_steps').attr('disabled', true);
            warn_ass.show()
	    $('.expression_steps').attr('disabled', true)
	    break;
	case "paired":
	    $('#jobfile').removeAttr('disabled')
	    $('#jobfile2').removeAttr('disabled')
	    $('#jobfile3').attr('disabled','disabled')
            reads_1.children("label").text("Left reads file:")
            reads_1.show()
            reads_2.show()
	    assembly_in.hide()
            $('.cleaning_steps').attr('disabled', false);
            $('.assembly_steps').attr('disabled', false);
	    warn_read.hide()
	    warn_read2.hide()
            $('.mapping_steps').attr('disabled', true);
            $('.identification_steps').attr('disabled', true);
            warn_ass.show()
	    $('.expression_steps').attr('disabled', true)
	    break;
	case "contigs":
	    $('#jobfile3').removeAttr('disabled')
	    $('#jobfile').attr('disabled','disabled')
	    $('#jobfile2').attr('disabled','disabled')
            reads_1.hide()
            reads_2.hide()
	    assembly_in.show()
            $('.cleaning_steps').attr('disabled', true);
            $('.assembly_steps').attr('disabled', true);
	    warn_read.show()
	    warn_read2.show()
            $('.mapping_steps').attr('disabled', true);
            $('.identification_steps').attr('disabled', false);
            warn_ass.hide()
	    $('.expression_steps').attr('disabled', true)
	    break;
	case "contigs_with_single":
	    $('#jobfile').removeAttr('disabled')
	    $('#jobfile2').attr('disabled','disabled')
	    $('#jobfile3').removeAttr('disabled')
            reads_1.children("label").text("Single reads file:")
	    reads_1.show()
	    assembly_in.show()
            reads_2.hide()
            $('.cleaning_steps').attr('disabled', false);
            $('.assembly_steps').attr('disabled', true);
	    warn_read.hide()
	    warn_read2.show()
            $('.mapping_steps').attr('disabled', false);
            $('.identification_steps').attr('disabled', false);
            warn_ass.hide()
	    $('.expression_steps').attr('disabled', false)
	    break;
	case "contigs_with_paired":
	    $('#jobfile').removeAttr('disabled')
	    $('#jobfile2').removeAttr('disabled','disabled')
	    $('#jobfile3').removeAttr('disabled')
	    reads_1.children("label").text("Left reads file:")
	    reads_1.show()
            reads_2.show()
	    assembly_in.show()
            $('.cleaning_steps').attr('disabled', false);
            $('.assembly_steps').attr('disabled', true);
	    warn_read.hide()
	    warn_read2.show()
            $('.mapping_steps').attr('disabled', false);
            $('.identification_steps').attr('disabled', false);
            warn_ass.hide()
	    $('.expression_steps').attr('disabled', false)
	    break;
	}
    });
});

// activate/desactivate mapping/identification steps
$(function (){
    var trin_check = $("input[id=trinity]")
    var warn_ass = $('div[id=no_assembly_alert]')
    trin_check.change(function(){
	if (trin_check.is(':checked'))
	{
            $('.mapping_steps').attr('disabled', false);
            $('.identification_steps').attr('disabled', false);
            $('.expression_steps').attr('disabled', false);
            warn_ass.hide()
	}
	else
        {
            $('.mapping_steps').attr({'disabled': true, 'checked': false});
            $('.identification_steps').attr({'disabled': true, 'checked': false});
            $('.expression_steps').attr({'disabled': true, 'checked': false});
            warn_ass.show()
        }

    });
});

$('#example').popover({html:true})
