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
        url: '/web/ajax/me',
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
	var filechk = checkFile( input )

	if ( size <= 0 || ! filechk ){
            showError( "No file has been uploaded")}
    	else if ( size < 512*1024*1024 ){
	    sendLittleFile()
	}else{
            sendBigFile()
        }
    });

}(window.jQuery);

function checkFile( input ){

    var ext_dict = {
	"fast" : ["fastq","fq"],
	"tgz_fast" : ["gz"],
	"assem" : ["fas","fasta","fa"],
	"seq_db_nuc" : ["fas","fasta","fa"],
	"seq_db_aa" : ["fas","fasta","fa"],
	"map_assem" : ["bam"],
	"hmm_profile" : ["hmm"]
    };

    var filetype = $("#filetype").val()
    var filename = input.files[0].name
    var extension = filename.split(".").pop()

    var filelist = []
    $('#filelist li').each(function(){
	filelist.push($(this).text())
    });
    
    // check if duplicate
    if( $.inArray( filename, filelist ) != -1 ){
	showError( "A file with the name " + filename + " is already in your file list. If this is a different file, please rename it before uploading.")
	
	// check if filetype specified
    }else if($("#filetype").val() == "undef"){
	showError("Please choose a format for the input before clicking 'Upload'");

	// check if correct extension
    }else if( $.inArray( extension, ext_dict[ filetype ]) == -1 ){
	
    	showError("The extension of your file is " 
		  + "." + extension
		  + " while the allowed extension(s) for the file format "
		  + "you have selected is(are) only: "
		  + "." + ext_dict[ filetype ].join(" or ."))
    }else{
	return true
    }
    return false
}

function getFileSize( input ){

    if( ! window.FileReader) {
        showError( "The file API isn't supported on this browser yet." );
    }else if( ! input ){
        showError( "Couldn't find the file input element." );
    }else if( ! input.files ){
        showError( "This browser doesn't support the `files` property of file inputs.");
    }else if( ! input.files[0] ){
        showError( "Please select a file before clicking 'Upload'" );
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

    xhr.open( 'PUT', '/web/ajax/file', true );

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

        xhr.open( 'PUT', '/web/ajax/filepart', true );

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

    xhr.open( 'PUT', '/web/ajax/filepart', true )

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

    xhr.open( 'PUT', '/web/ajax/filepart', true )

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
        url: '/web/ajax/file',
        success: function( data ) { f_ok( data['files'] ) }
    });
}

function getFileListWithType( ftype, f_ok ){
    var tname = typeof ftype
    if( tname == "number" ){
        $.ajax({
            dataType: "json",
            data: { filetype: ftype },
            url: '/web/ajax/file',
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
            url: '/web/ajax/file',
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
                items.push('<li>' + val['juid'] + ': <a href="/web/job/' + val['id'] + '">' + val['name']
                           + '</a></li>');
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


//    <!-- Scroll down when clicking on the accordion -->
    // $('.accordion-toggle').click(function (e) {
    //     e.preventDefault();
    //     var n = $(document).height();
    //     $('html, body').animate({ scrollTop: n/2 },'500');
    // });

    // <!-- Enable tabs -->
    // $('#myTab a').click(function (e) {
    //  e.preventDefault();
    //  $(this).tab('show');
    // })

$('#example').popover({html:true})
