$(document).ready(function() {

    generateShade();
    generateSearch();
    generatePages();

    var limit = parseInt($('#limit').children('option:selected').data('command'));
    var current = 0;
    var listcount = parseInt($('#listcount').val());
    var pagecount = Math.floor(listcount / limit);
    var activepage = 0;
    var searchvalue = '';
    var getList;
    var command;
    var tableList = $('.paginate-table table tbody');
    var commandList = tableList.find('tr:eq(0) td:last()').html();
    var fieldsList = $('.paginate-table').data('rows').split(",");

    $('.paginate-search-button').attr('disabled',true);
    pages(command);
    markpage(0,0);

    //to fix later
    //pagination for search
    //scrollable table
    //disable buttons (prev, next)
    //allow all limit
    //multiple click handler

    $(document).on('click', '.paginate-nav, .paginate-page, .paginate-search-button', function() {
        paginate($(this));
    });
    $(document).on('change', '.paginate-limit', function() {
        paginate($(this));
    });

    $('.paginate-search').keyup(function(){
        if($(this).val().length !=0){
            $('.paginate-search-button').attr('disabled', false);
        }
        else{
            $('.paginate-search-button').attr('disabled',true);
            paginate($('.paginate-search-button-clear'));
        }
    });
    $('.paginate-search-button-clear').on('click', function(){
        $('.paginate-search').val('');
        paginate($(this));
    });

    function paginate(obj){
        var current = parseInt($('#current').val());

        if(obj.data('command') == "prev"){
            if((current - limit) <= 0){
                current = 0;
            }
            else{
                current = current - limit;
            }
        }
        else if(obj.data('command') == "next"){
            if((current + limit) < listcount){
                current = current + limit;
            }
        }
        else if(obj.hasClass('pages')){
            current = (parseInt(obj.data('command')) * limit) - limit;
        }

        if(obj.data('command') == null){
            command = parseInt($('#limit').children('option:selected').data('command'));
        }
        else{
            command = obj.data('command');
        }
        limit = parseInt($('#limit').children('option:selected').data('command'));

        searchvalue = $('.paginate-search').val();
        if(searchvalue == '' || searchvalue == null){
            searchvalue = 'null';
        }

        var url = "page/" + command + "/" + current + "/" + limit + "/" + convertToSlug(searchvalue);

        $('#shade').fadeIn();
        getList = $.getJSON(url, function(result) {

            $('#current').val(current);

            tableList.html('');

            if(result.length > 0){

                if(command == "search"){
                    arraylimit = result.length;
                    $('#pages').html('');
                }
                else{
                    arraylimit = limit;
                }

                for (var i = 0; i < arraylimit; i++) {

                    tableList.append("<tr><td>" + result[i].pk + "</td></tr>");

                    for (var j = 0; j < fieldsList.length; j++) {
                        tableList.find('tr').eq(i).last('td').append("<td>" + result[i].fields[fieldsList[j]] + "</td>");
                    }

                    tableList.find('tr').eq(i).last('td').append("<td>" + commandList + "</td>");

                    commandLink = tableList.find('tr').eq(i).last('td');
                    oldPk = commandLink.find('a:eq(0)').attr("href").replace( /^\D+/g, '');
                    commandLink.find('a:eq(0)').attr("href", commandLink.find('a:eq(0)').attr("href").replace(oldPk, result[i].pk + "/"));
                    commandLink.find('a:eq(1)').attr("href", commandLink.find('a:eq(1)').attr("href").replace(oldPk, result[i].pk + "/"));
                    commandLink.find('a:eq(2)').attr("href", commandLink.find('a:eq(2)').attr("href").replace(oldPk, result[i].pk + "/"));

                    $('#shade').fadeOut();
                }
                if(command == "search"){
                    $('#pagination-container').hide();
                }
                else{
                    $('#pagination-container').show();
                    pages(command);
                    markpage(current, limit);
                }
            }
            else{
                tableList.append("<tr><td colspan='100%'> No result found </td>" + "</tr>");
                $('#shade').fadeOut();
                $('#pagination-container').hide();
            }
        }).fail(function() {
            console.log("error");

            tableList.html('');
            tableList.append("<tr><td colspan='100%'> No result found </td>" + "</tr>");
            $('#shade').fadeOut();
        });
    }

    function markpage(current, limit){
        if(current == 0 && limit == 0){
            activepage = 0;
        }
        else{
            activepage = parseInt(Math.floor((current + limit) / limit)) - 1;
        }

        $('.paginate-page').removeClass('active').eq(activepage).addClass('active');

        if(activepage < 3){
            $('.paginate-page').slice(0, 7).removeClass('hidden');
        }
        else{
            $('.paginate-page').slice((activepage - 3), (activepage + 4)).removeClass('hidden');
        }
    }

    function convertToSlug(Text){
        return Text
            .toLowerCase()
            .replace(/ /g,'-')
            .replace(/[^\w-]+/g,'');
    }

    function pages(command){
        limit = parseInt($('#limit').children('option:selected').data('command'));
        pagecount = Math.floor(listcount / limit);
        if(listcount%limit != 0){
            pagecount = pagecount + 1;
        }

        $('#pages').html('');
        $('#pages').prepend("<li data-command='prev' class='prev paginate paginate-nav'><a title='Prev' ><i class='fa fa-angle-left'></i></a></li>");
        for (var j = 1; j <= pagecount; j++){
            $('#pages').append("<li data-command='" + j + "' class='paginate paginate-page pages hidden'><a>"+ j +"</a></li>");
        }
        $('#pages').append("<li data-command='next' class='next paginate paginate-nav'><a title='Next' ><i class='fa fa-angle-right'></i></a></li>");
    }

    function generateShade(){
        $('.paginate-table table').before("<div id='shade'><div class='loader two-color'></div></div>");
        $('.paginate-table .table-responsive').css({'position': 'relative'});
    }

    function generateSearch(){
        $('.paginate-table h4').after("<div id='search-container' class='col-md-3 col-sm-4 col-xs-3 pull-right'>" +
                                        "<div class='input-group'>" +
                                            "<input type='text' class='paginate-search form-control' placeholder='Search...'>" +
                                            "<span class='input-group-btn'>" +
                                                "<button class='btn btn-info waves-effect waves-light paginate-search-button' data-command='search'>" +
                                                    "<span class='icon_search' aria-hidden='true'></span>" +
                                                "</button>" +
                                            "</span>" +
                                        "</div>" +
                                    "</div>");
    }

    function generatePages(){
        $('.paginate-table').append("<div class='row' style='text-align: right'>" +
                                        "<div id='pagination-container' class='pull-right col-md-5 col-sm-8 col-xs-9'>" +
                                            "<select id='limit' class='form-control paginate paginate-limit'> " +
                                                "<option data-command='10'>10</option> " +
                                                "<option data-command='50'>50</option> " +
                                                "<option data-command='10'>100</option>" +
                                            "</select>&nbsp;&nbsp;&nbsp;" +
                                            "<ul id='pages' class='pagination' style='visibility: visible;'></ul>" +
                                            "<input type='hidden' id='current' value='0'>" +
                                            "<input type='hidden' id='listcount'>" +
                                        "</div>" +
                                    "</div>");
        $('#listcount').val($('.paginate-table').data('list'));
    }
});