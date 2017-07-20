!function (window, document, $) {
    "use strict";

    //datepicker
    $(".datepicker").datepicker({
        autoclose: true,
        format: 'yyyy-mm-dd'
    });

    // set 7 days before as minDate for class .datepicker.week
    var d = new Date();
    d.setDate(d.getDate() - 7);
    $('.datepicker.week').each(function(){
        $(this).datepicker('setStartDate', d);
    });

    // datepicker range
    $('.datepickerfrom').each(function () {
        $(this).datepicker({
            autoclose: true,
            format: 'yyyy-mm-dd'
        }).on('changeDate', function (selected) {
            var minDate = new Date(selected.date.valueOf());
            $('.datepickerto:eq(' + $(this).index('.datepickerfrom') + ')').datepicker('setStartDate', minDate);
        });
    });
    $('.datepickerto').each(function () {
        $(this).datepicker({
            autoclose: true,
            format: 'yyyy-mm-dd'
        }).on('changeDate', function (selected) {
            var minDate = new Date(selected.date.valueOf());
            $('.datepickerfrom:eq(' + $(this).index('.datepickerto') + ')').datepicker('setEndDate', minDate);
        });
    });
    $(document).ready(function () {
        if ($(".datepickerfrom").val() != '' && $(".datepickerto").val() != '') {
            $('.datepickerfrom').each(function () {
                var datepickerto = $('.datepickerto:eq('+$(this).index('.datepickerfrom')+')');
                var minDate = new Date($(this).val());
                datepickerto.datepicker('setStartDate', minDate);
                minDate = new Date(datepickerto.val());
                $(this).datepicker('setEndDate', minDate);
            });
        }
    });
}(window, document, jQuery);

