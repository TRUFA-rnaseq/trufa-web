!function ($) {
    "use strict"; // jshint ;_;

    if( $( '#blat_menu1').length ){
        fillupBlatMenu1()
    }

    
}(window.jQuery);


function fillupBlatMenu1(){
    getFileListWithType( 1, function( files ){
        var items1 = [];

        $.each(files, function( key, val ) {
            items1.push( "<li role=\"presentation\"><a role=\"menuitem\" tabindex=\"-1\" href=\"#\"> "+ val['file'] + "</a></li>" )
        });

        $( '#blat_menu1').append( items1 );
    });
}
