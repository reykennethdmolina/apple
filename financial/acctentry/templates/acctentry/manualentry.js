
    $('#detail_chartofaccount').change(function() {
    $("#v_detail_bankaccount").addClass('hide');
    $("#detail_bankaccount").removeAttr('required');
    $("#v_detail_department").addClass('hide');
    $("#detail_department").removeAttr('required');
    $("#v_detail_employee").addClass('hide');
    $("#detail_employee").removeAttr('required');
    $("#v_detail_supplier").addClass('hide');
    $("#detail_supplier").removeAttr('required');
    $("#v_detail_customer").addClass('hide');
    $("#detail_customer").removeAttr('required');
    $("#v_detail_unit").addClass('hide');
    $("#detail_unit").removeAttr('required');
    $("#v_detail_branch").addClass('hide');
    $("#detail_branch").removeAttr('required');
    $("#v_detail_product").addClass('hide');
    $("#detail_product").removeAttr('required');
    $("#v_detail_inputvat").addClass('hide');
    $("#detail_inputvat").removeAttr('required');
    $("#v_detail_outputvat").addClass('hide');
    $("#detail_outputvat").removeAttr('required');
    $("#v_detail_vat").addClass('hide');
    $("#detail_vat").removeAttr('required');
    $("#v_detail_wtax").addClass('hide');
    $("#detail_wtax").removeAttr('requiredn');
    $("#v_detail_ataxcode").addClass('hide');
    $("#detail_ataxcode").removeAttr('required');
    $.ajax({
        url: "{% url 'acctentry:checkchartvalidatetion' %}",
        type: "post",
        dataType: "json",
        data: {
            'csrfmiddlewaretoken': "{{csrf_token}}",
            'chartid':  $('#detail_chartofaccount').val(),
        },
        success: function(response){
            chart = response.chart;
            chartdata = $.parseJSON(chart);
            //console.log(chartdata[0].fields['bankaccount_enable']);
            if (chartdata[0].fields['bankaccount_enable'] == 'Y') {
                $("#v_detail_bankaccount").removeClass('hide');
                $("#detail_bankaccount").attr('required', 'required');;
            }
            //console.log(chartdata[0].fields['department_enable']);
            if (chartdata[0].fields['department_enable'] == 'Y') {
                $("#v_detail_department").removeClass('hide');
                $("#detail_department").attr('required', 'required');;
            }
            //console.log(chartdata[0].fields['employee_enable']);
            if (chartdata[0].fields['employee_enable'] == 'Y') {
                $("#v_detail_employee").removeClass('hide');
                $("#detail_employee").attr('required', 'required');;
            }
            //console.log(chartdata[0].fields['supplier_enable']);
            if (chartdata[0].fields['supplier_enable'] == 'Y') {
                $("#v_detail_supplier").removeClass('hide');
                $("#detail_supplier").attr('required', 'required');;
            }
            //console.log(chartdata[0].fields['customer_enable']);
            if (chartdata[0].fields['customer_enable'] == 'Y') {
                $("#v_detail_customer").removeClass('hide');
                $("#detail_customer").attr('required', 'required');;
            }
            //console.log(chartdata[0].fields['unit_enable']);
            if (chartdata[0].fields['unit_enable'] == 'Y') {
                $("#v_detail_unit").removeClass('hide');
                $("#detail_unit").attr('required', 'required');;
            }
            //console.log(chartdata[0].fields['branch_enable']);
            if (chartdata[0].fields['branch_enable'] == 'Y') {
                $("#v_detail_branch").removeClass('hide');
                $("#detail_branch").attr('required', 'required');;
            }
            //console.log(chartdata[0].fields['product_enable']);
            if (chartdata[0].fields['product_enable'] == 'Y') {
                $("#v_detail_product").removeClass('hide');
                $("#detail_product").attr('required', 'required');;
            }
            //console.log(chartdata[0].fields['inputvat_enable']);
            if (chartdata[0].fields['inputvat_enable'] == 'Y') {
                $("#v_detail_inputvat").removeClass('hide');
                $("#detail_inputvat").attr('required', 'required');;
            }
            //console.log(chartdata[0].fields['outputvat_enable']);
            if (chartdata[0].fields['outputvat_enable'] == 'Y') {
                $("#v_detail_outputvat").removeClass('hide');
                $("#detail_outputvat").attr('data-validation', 'required');;
            }
            //console.log(chartdata[0].fields['vat_enable']);
            if (chartdata[0].fields['vat_enable'] == 'Y') {
                $("#v_detail_vat").removeClass('hide');
                $("#detail_vat").attr('required', 'required');;
            }
            //console.log(chartdata[0].fields['wtax_enable']);
            if (chartdata[0].fields['wtax_enable'] == 'Y') {
                $("#v_detail_wtax").removeClass('hide');
                $("#detail_wtax").attr('required', 'required');;
            }
            //console.log(chartdata[0].fields['ataxcode_enable']);
            if (chartdata[0].fields['ataxcode_enable'] == 'Y') {
                $("#v_detail_ataxcode").removeClass('hide');
                $("#detail_ataxcode").attr('required', 'required');;
            }

            unit = response.unit;
            unitlist = $.parseJSON(unit);

            //console.log(unitlist);
            var unitoptions = '<option value="">-- Select Unit --</option>';
            $.each(unitlist, function (k, v) {
                //console.log(v.fields.code);
                unitoptions += '<option value="' + v.fields.pk + '">' + v.fields.description + '</option>';
            });
            $("#detail_unit").html(unitoptions);
            $("#detail_unit option:first").attr('selected', 'selected');
            $("#detail_unit").attr('disabled', false);


        }, error: function(response) {
            console.debug(reponse);
        }
    })
});