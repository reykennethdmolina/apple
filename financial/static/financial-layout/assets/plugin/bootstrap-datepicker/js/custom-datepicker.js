!function (window, document, $) {
    "use strict";

    //datepicker
    $(".datepicker").datepicker({
        autoclose: true,
        format: 'yyyy-mm-dd',
        orientation: 'bottom'
    });

    // set 7 days before as minDate for class .datepicker.week
    var d = new Date();
    d.setDate(d.getDate() - 7);
    $('.datepicker.week').each(function(){
        $(this).datepicker('setStartDate', d);
    });

    initializeDateRange();

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
        $('.datepickerfrom_month').each(function () {
            if ($('.datepickerfrom_month:eq('+$(this).index('.datepickerfrom_month')+')').val() != '' && $('.datepickerto_month:eq('+$(this).index('.datepickerfrom_month')+')') != '') {
                var datepickerto_month = $('.datepickerto_month:eq('+$(this).index('.datepickerfrom_month')+')');
                var minDate = new Date($(this).val());
                datepickerto_month.datepicker('setStartDate', minDate);
                minDate = new Date(datepickerto_month.val());
                $(this).datepicker('setEndDate', minDate);
            }
        });
    });
}(window, document, jQuery);

function initializeDateRange(){
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

    $('.datepickerfrom_month').each(function () {
        $(this).datepicker({
            autoclose: true,
            format: 'yyyy-mm-dd'
        }).on('changeDate', function (selected) {
            var minDate = new Date(selected.date.valueOf());
            var wholeDate = new Date(selected.date);
            var maxDate = new Date(wholeDate.setDate(wholeDate.getDate() + 31));
            $('.datepickerto_month:eq(' + $(this).index('.datepickerfrom_month') + ')').datepicker('setStartDate', minDate);
            $('.datepickerto_month:eq(' + $(this).index('.datepickerfrom_month') + ')').datepicker('setEndDate', maxDate);
        });
    });
    $('.datepickerto_month').each(function () {
        $(this).datepicker({
            autoclose: true,
            format: 'yyyy-mm-dd'
        }).on('changeDate', function (selected) {
            var minDate = new Date(selected.date.valueOf());
            var wholeDate = new Date(selected.date);
            var maxDate = new Date(wholeDate.setDate(wholeDate.getDate() - 31));
            $('.datepickerfrom_month:eq(' + $(this).index('.datepickerto_month') + ')').datepicker('setEndDate', minDate);
            $('.datepickerfrom_month:eq(' + $(this).index('.datepickerto_month') + ')').datepicker('setStartDate', maxDate);
        });
    });
}

