/* = REGISTER ================================================================== */
!function ($){
    "use strict"; // jshint ;_;

    validRegister()

}(window.jQuery);

function validRegister(){
    $("#register").validate({
	rules:{
	    user_name:"required",
	    user_email:{required:true,email: true},
	    pwd:{required:true,minlength: 6},
	    cpwd:{required:true,equalTo: "#pwd"},
	},

	messages:{
	    user_name:"Enter a user name",
	    user_email:{
		required:"Enter your email address",
		email:"Enter valid email address"},
	    pwd:{
		required:"Enter your password",
		minlength:"Password must be minimum 6 characters"},
	    cpwd:{
		required:"Confirm your password",
		equalTo:"Password and confirm password are not matching"},
	},

	errorClass: "help-inline",
	errorElement: "span",
	highlight:function(element, errorClass, validClass)
	{
	    $(element).parents('.control-group').removeClass('success');
	    $(element).parents('.control-group').addClass('error');
	},
	unhighlight: function(element, errorClass, validClass)
	{
	    $(element).parents('.control-group').removeClass('error');
	    $(element).parents('.control-group').addClass('success');
	}
    });
};



