!function ($) {
    "use strict"; // jshint ;_;

    $('#update-button').click( function(){
        var formstr = $('#setupform').serialize();

        $.ajax({
            dataType: "json",
            url: '/web/ajax/me',
            type: 'PUT',
            data: formstr,

            success: function( data ) {
                $('#setupform input').val('')
                showClear()
                if( data['ok'] ){
                    showOK( "Password Changed" )
                }else{
                    showError( data['msg'] )
                }
            }
        });
    });

}(window.jQuery);
