$(function(){
   // input type = number
   $("input[type=number]").keydown(function (e) {
        if ($.inArray(e.keyCode, [46, 8, 9, 27, 13, 110, 190]) !== -1 ||
            (e.keyCode === 65 && (e.ctrlKey === true || e.metaKey === true)) ||
            (e.keyCode >= 35 && e.keyCode <= 40)) {
                 return;
        }
        if ((e.shiftKey || (e.keyCode < 48 || e.keyCode > 57)) && (e.keyCode < 96 || e.keyCode > 105)) {
            e.preventDefault();
        }
    });

});

// custom-alert
$(".custom-alert").each(function(){
    alert_content = $(this).text();
    alert_id = $(this).attr('id');
    alert_class = "alt-info alert-info";

    if($(this).hasClass('success')) alert_class = "alt-success alert-success";
    else if($(this).hasClass('danger')) alert_class = "alt-danger alert-danger";
    else if($(this).hasClass('warning')) alert_class = "alt-danger alert-warning";

    $('body').append("<div id='"+alert_id+"' class='custom-alert alert dark "+alert_class+" fade' role='dialog'> " +
                        "<button type='button' class='close' data-dismiss='modal' aria-label='Close'> " +
                            "<i class='icon fa-close' aria-hidden='true'></i> " +
                        "</button>" +
                        alert_content + "&nbsp;&nbsp;&nbsp;&nbsp;" +
                    "</div>");
    $(this).remove();
});
function customAlert(e){
    e.modal('show');
    setTimeout(function() { e.modal('hide'); }, 2000);
}

// Ajax paginate
$.endlessPaginate();