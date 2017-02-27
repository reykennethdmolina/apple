/**
 * Created by Grace Villanueva on 2/21/2017.
 */

$( "#validateButton" ).click(function() {
    if($('.validateIntFormMask').length){
        $('.validateIntFormMask').each(function(){
            if($('.validateIntFormMask').val().length > 0 &&($('.validateIntFormMask').val().indexOf(' ') >= 0 ||
                $('.validateIntFormMask').val().indexOf('t') >= 0)){
                $('.validateIntFormMask').val("");
            }
        });
    }
});
