// -----------------------------------------------------------------------------
!function ($) {
    "use strict"; // jshint ;_;

    if( $( '#blat_menu0').length ){
        fillupBlatMenu0()
    }
    if( $( '#blat_menu1').length ){
        fillupBlatMenu1()
    }
    if( $( '#blat_menu2').length ){
        fillupBlatMenu2()
    }
    if( $( '#hmm_menu0').length ){
        fillupHmmerMenu0()
    }

    initNumberAndTypeJobInput()
    setupMappingSteps()
    summarizeForm()

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

}(window.jQuery);

// -----------------------------------------------------------------------------
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

// -----------------------------------------------------------------------------
function fillupBlatMenu1(){
    getFileListWithType( 3, function( files ){
        var items1 = [];

        var count = 0
        $.each(files, function( key, val ) {

            items1.push( "<li role=\"presentation\"><input type='checkbox' class='identification_steps' name='blat_custom_ass_n'" + count + "' value=" + val['file'] + " href=\"#\" disabled> " + val['file'] + "</li>" )

            count = count + 1
        });

        $( '#blat_menu1').append( items1 );
    });
}

// -----------------------------------------------------------------------------
function fillupBlatMenu2(){
    getFileListWithType( 4, function( files ){
        var items1 = [];

    var count = 0
        $.each(files, function( key, val ) {

            items1.push( "<li role=\"presentation\"><input type='checkbox' class='identification_steps' name='blat_custom_ass_aa'" + count + "' value=" + val['file'] + " href=\"#\" disabled> " + val['file'] + "</li>" )

        count = count + 1
        });

        $( '#blat_menu2').append( items1 );
    });
}

// -----------------------------------------------------------------------------
function fillupHmmerMenu0(){
    getFileListWithType( 7, function( files ){
        var items1 = [];

    var count = 0
        $.each(files, function( key, val ) {

            items1.push( "<li role=\"presentation\"><input type='checkbox' class='identification_steps' name='hmm_custom'" + count + "' value=" + val['file'] + " href=\"#\" disabled> " + val['file'] + "</li>" )

        count = count + 1
        });

        $( '#hmm_menu0').append( items1 );
    });
}

// -----------------------------------------------------------------------------
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

// -----------------------------------------------------------------------------
function initNumberAndTypeJobInput(){
    // Select the number and type of input:
    var reads_1 = $("div[id=reads_1]")
    var reads_2 = $("div[id=reads_2]")
    var assembly_in = $("div[id=assembly_in]")
    var in_type = $("input[name=input_type]")

    // Setting single or paired reads
    in_type.change(function (){
        // unchecking all boxes
        $('.cleaning_steps').attr('checked', false)
        $('.assembly_steps').attr('checked', false)
        $('.assembly_qc_steps').attr('checked', false)
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
	var warn_exp = $('div[id=no_reads_and_ass_alert]')

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
            $('.assembly_qc_steps').attr('disabled', true);
            $('.mapping_steps').attr('disabled', true);
            $('.identification_steps').attr('disabled', true);
            warn_ass.show()
            $('.expression_steps').attr('disabled', true)
	    warn_exp.show()
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
            $('.assembly_qc_steps').attr('disabled', true);
            $('.mapping_steps').attr('disabled', true);
            $('.identification_steps').attr('disabled', true);
            warn_ass.show()
            $('.expression_steps').attr('disabled', true)
	    warn_exp.show()
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
            $('.assembly_qc_steps').attr('disabled', false);
            $('.mapping_steps').attr('disabled', true);
            $('.identification_steps').attr('disabled', false);
            warn_ass.hide()
            $('.expression_steps').attr('disabled', true)
	    warn_exp.show()
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
            $('.assembly_qc_steps').attr('disabled', false);
            $('.mapping_steps').attr('disabled', false);
            $('.identification_steps').attr('disabled', false);
            warn_ass.hide()
            $('.expression_steps').attr('disabled', false)
	    warn_exp.hide()
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
            $('.assembly_qc_steps').attr('disabled', false);
            $('.mapping_steps').attr('disabled', false);
            $('.identification_steps').attr('disabled', false);
            warn_ass.hide()
            $('.expression_steps').attr('disabled', false)
	    warn_exp.hide()
            break;
        }
    });
}

// -----------------------------------------------------------------------------
function setupMappingSteps(){
    // activate/desactivate mapping/identification steps
    var trin_check = $("input[id=trinity]")
    var warn_ass = $('div[id=no_assembly_alert]')
    var warn_exp = $('div[id=no_reads_and_ass_alert]')

    trin_check.change(function(){
        if (trin_check.is(':checked')){
            $('.mapping_steps').attr('disabled', false);
            $('.assembly_qc_steps').attr('disabled', false);
            $('.identification_steps').attr('disabled', false);
            $('.expression_steps').attr('disabled', false);
            warn_ass.hide()
	    warn_exp.hide()
        }else{
            $('.mapping_steps').attr({'disabled': true, 'checked': false});
            $('.assembly_qc_steps').attr({'disabled': true, 'checked': false});
            $('.identification_steps').attr({'disabled': true, 'checked': false});
            $('.expression_steps').attr({'disabled': true, 'checked': false});
            warn_ass.show()
	    warn_exp.show()
        }

    });
}
// -----------------------------------------------------------------------------
function summarizeForm(){

    $('#jobform :input').change(function(){
	$("#formsum").empty()

	$("#formsum").append("<h4>Summary of the selected steps:")
	$("#formsum").append("<h5>Cleaning step:")
	$(".cleaning_steps").each(function(){
 	     if ( $(this).is(':checked')) {
		var val = $(this).val()
		var name = $(this).attr('name')
		$("#formsum").append("<li>" + name + ":" + val + "</li>")
	    }
	});

	$("#formsum").append("<h5>Assembly/Mapping step:")	
	$(".assembly_steps, .assembly_qc_steps, .mapping_steps").each(function(){
	    if ( $(this).is(':checked')) {
		var val = $(this).val()
		var name = $(this).attr('name')
		$("#formsum").append("<li>" + name + ":" + val + "</li>")
	    }
	});
	$("#formsum").append("<h5>Identification step:")	
	$(".identification_steps").each(function(){
	    if ( $(this).is(':checked')) {
		var val = $(this).val()
		var name = $(this).attr('name')
		$("#formsum").append("<li>" + name + ":" + val + "</li>")
	    }
	});
	$("#formsum").append("<h5>Expression step:")	
	$(".expression_steps").each(function(){
	    if ( $(this).is(':checked')) {
		var val = $(this).val()
		var name = $(this).attr('name')
		$("#formsum").append("<li>" + name + ":" + val + "</li>")
	    }
	});
    });
}