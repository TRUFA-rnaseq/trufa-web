!function ($) {
    "use strict"; // jshint ;_;

    if( $('#jobname').length ){
        $('#jobname').click( editJobName )
    }

    if( $('#jobnameicon').length ){
        $('#jobnameicon').click( editJobName )
    }

    if( $('#btncanceljob').length ){
        $('#btncanceljob').click( cancelJob )
    }

    if( $('#canceljobyes').length ){
        $('#canceljobyes').click( cancelJobYes )
    }

    if( $('#canceljobno').length ){
        $('#canceljobno').click( cancelJobNo )
    }

}(window.jQuery);

function editJobName(){
    $('#jobnameicon').addClass('hidden')
    oldname = $('#jobname').text()
    $('#jobname').replaceWith("<input name='newname' type='text' value='" + 
                              oldname + "' id='jobnameinput' />")
    $('#jobnameinput').focus()
    $('#jobnameinput').focusout( editJobNameDone )

    $('#jobnameinput').change( editJobNameDone )
}

function editJobNameDone(){
    $('#jobnameicon').removeClass('hidden')
    if( $('#jobnameinput').length ){
        newname = $('#jobnameinput').val()

        var xhr = new XMLHttpRequest();
        xhr.onreadystatechange = function( e ){
            if( 4 == this.readyState ){
            }
        }

        xhr.open( 'PUT', '/ajax/jobname', true );

        var form = $('#jobnameform')[0];
        var fd = new FormData( form );
        xhr.send( fd );

        $('#jobnameinput').replaceWith("<span id='jobname'>" +
                                       newname + "</span>")

        $('#jobname').click( editJobName )
    }
}

function cancelJob(){
    $('#cancelmodal').modal('show')
}

function cancelJobYes(){
    $('#cancelmodal').modal('hide')
    alert("Cancel YES")
}

function cancelJobNo(){
    $('#cancelmodal').modal('hide')
    alert("Cancel NO")
}
