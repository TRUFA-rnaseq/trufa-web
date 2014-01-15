!function ($) {
    "use strict"; // jshint ;_;

    if( $( '#blat_menu0').length ){
        fillupBlatMenu0()
    }
    if( $( '#blat_menu1').length ){
        fillupBlatMenu1()
    }
    if( $( '#hmm_menu0').length ){
        fillupHmmerMenu0()
    }



    
}(window.jQuery);

function fillupBlatMenu0(){
    getFileListWithType( 3, function( files ){
        var items1 = [];

	var count = 0
        $.each(files, function( key, val ) {

// this currently defines an array but dont get all values in (just one)
//            items1.push( "<li role=\"presentation\"><input type='checkbox' name='my_blat_custom[]' value=" + val['file'] + " href=\"#\"> " + val['file'] + "</li>" )
            items1.push( "<li role=\"presentation\"><input type='checkbox' class='cleaning_steps' name='blat_custom_reads_n'" + count + "' value=" + val['file'] + " href=\"#\" disabled> " + val['file'] + "</li>" )
	    count = count + 1
        });

        $( '#blat_menu0').append( items1 );
    });
}

function fillupBlatMenu1(){
    getFileListWithType( 3, function( files ){
        var items1 = [];

	var count = 0
        $.each(files, function( key, val ) {

// this currently defines an array but dont get all values in (just one)
//            items1.push( "<li role=\"presentation\"><input type='checkbox' name='my_blat_custom[]' value=" + val['file'] + " href=\"#\"> " + val['file'] + "</li>" )
            items1.push( "<li role=\"presentation\"><input type='checkbox' class='cleaning_steps' name='blat_custom_ass_n'" + count + "' value=" + val['file'] + " href=\"#\" disabled> " + val['file'] + "</li>" )

	    count = count + 1
        });

        $( '#blat_menu1').append( items1 );
    });
}

function fillupHmmerMenu0(){
    getFileListWithType( 6, function( files ){
        var items1 = [];

	var count = 0
        $.each(files, function( key, val ) {

// this currently defines an array but dont get all values in (just one)
//            items1.push( "<li role=\"presentation\"><input type='checkbox' name='my_blat_custom[]' value=" + val['file'] + " href=\"#\"> " + val['file'] + "</li>" )
            items1.push( "<li role=\"presentation\"><input type='checkbox' class='cleaning_steps' name='blat_custom_ass_n'" + count + "' value=" + val['file'] + " href=\"#\" disabled> " + val['file'] + "</li>" )

	    count = count + 1
        });

        $( '#hmm_menu0').append( items1 );
    });
}
