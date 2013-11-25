!function ($) {
    "use strict"; // jshint ;_;

    if( $( '#blat_menu1').length ){
        fillupBlatMenu1()
    }

    
}(window.jQuery);

// function fillupBlatMenu1(){
//     getFileListWithType( 3, function( files ){
//         var items1 = [];

//         $.each(files, function( key, val ) {
//             items1.push( "<li role=\"presentation\"><a role=\"menuitem\" tabindex=\"-1\" href=\"#\"> " + val['file'] + "</a></li>" )
//         });

//         $( '#blat_menu0').append( items1 );
//         $( '#blat_menu1').append( items1 );
//         $( '#blat_menu2').append( items1 );
//     });
// }

function fillupBlatMenu1(){
    getFileListWithType( 3, function( files ){
        var items1 = [];

        $.each(files, function( key, val ) {
	    a = {}
	    a.id = key
	    a.label = val['file']
            items1.push(a)
        });

	$(".myDropdownCheckbox").dropdownCheckbox({
	    data: items1,
	    title: "Available databases"
    });

    });
}

//var test = $("myselector").dropdownCheckbox("checked");


