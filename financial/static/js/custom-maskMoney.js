/**
 * Created by Grace Villanueva on 1/11/2017.
 */

$(function() {
	$('.amount').maskMoney();
});

$( "#validateButton" ).click(function() {
    if($('.amount').length){
        $('.amount').each(function(){
            var s = $(this).val().toString();
            var t = s.replace( /,/g, "");
            $(this).val(t);
        });
    }

});