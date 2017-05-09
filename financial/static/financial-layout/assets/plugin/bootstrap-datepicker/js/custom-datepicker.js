!function (window, document, $) {
    "use strict";
    $(".datepicker").datepicker({
        autoclose: true,
        format: 'yyyy-mm-dd'
    });
    $(".datepickerfrom").datepicker({
        autoclose: true,
        format: 'yyyy-mm-dd'
    }).on('changeDate', function (selected) {
        var minDate = new Date(selected.date.valueOf());
        $('.datepickerto').datepicker('setStartDate', minDate);
    });
    $(".datepickerto").datepicker({
        autoclose: true,
        format: 'yyyy-mm-dd'
    }).on('changeDate', function (selected) {
        var minDate = new Date(selected.date.valueOf());
        $('.datepickerfrom').datepicker('setEndDate', minDate);
    });
    $( document ).ready(function() {
      if($(".datepickerfrom").val() != '' && $(".datepickerto").val() != ''){
          var minDate = new Date($(".datepickerfrom").val());
          $('.datepickerto').datepicker('setStartDate', minDate);
          minDate = new Date($(".datepickerto").val());
          $('.datepickerfrom').datepicker('setEndDate', minDate);
      }
    });

    // set 7 days before as minDate for class .datepicker.week
    var d = new Date();
    d.setDate(d.getDate()-7);
    $('.datepicker.week').datepicker('setStartDate', d);
}(window, document, jQuery);

