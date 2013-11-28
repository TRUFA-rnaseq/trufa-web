!function ($) {
    "use strict"; // jshint ;_;

    if( $( '#blat_menu1').length ){
        fillupBlatMenu1()
    }

    
}(window.jQuery);

function fillupBlatMenu1(){
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
        $( '#blat_menu1').append( items1 );
        $( '#blat_menu2').append( items1 );
    });
}

// function fillupBlatMenu1(){
//     getFileListWithType( 3, function( files ){
//         var items1 = [];

//         $.each(files, function( key, val ) {
// 	    a = {}
// 	    a.id = key
// 	    a.label = val['file']
//             items1.push(a)
//         });

// 	$(".myDropdownCheckbox").dropdownCheckbox({
// 	    data: items1,
// 	    title: "Available databases"
//     });

//     });
// }

//var test = $("myselector").dropdownCheckbox("checked");


