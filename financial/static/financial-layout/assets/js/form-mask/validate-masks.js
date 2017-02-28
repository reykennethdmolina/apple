/**
 * Created by Grace Villanueva on 2/21/2017.
 */

$( "#validateButton" ).click(function() {
    if($('.validateIntFormMask').length){
        $('.validateIntFormMask').each(function(i, obj){
            if($(this).val().length > 0 &&($(this).val().indexOf(' ') >= 0 || $(this).val().indexOf('t') >= 0)){

                invalidInput = $(this).val();
                invalidForm = $(this);
                $(this).val("");

                window.setTimeout(function () {
                    invalidForm.val(invalidInput);
                }, 100);
            }
        });
    }
});
