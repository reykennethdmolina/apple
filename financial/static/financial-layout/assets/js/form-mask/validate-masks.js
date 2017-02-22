/**
 * Created by Grace Villanueva on 2/21/2017.
 */

$( "#validateButton" ).click(function() {
    if($('.tinNumber').length){
        $('.tinNumber').each(function(){
            if($('.tinNumber').val().indexOf(' ') >= 0){
                $('.tinNumber').val("");
            }
        });
    }

});
