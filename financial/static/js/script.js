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
function customAlert(e, duration){
    var def_duration = duration >= 0 ? duration : 4000;
    e.modal('show');
    setTimeout(function() { e.modal('hide'); }, def_duration);
}

// Ajax paginate
$.endlessPaginate();

// cookie
function getCookie(cname) {
    var name = cname + "=";
    var decodedCookie = decodeURIComponent(document.cookie);
    var ca = decodedCookie.split(';');
    for (var i = 0; i < ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0) == ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
            return c.substring(name.length, c.length);
        }
    }
    return "";
}
function setCookie(cname, cvalue, exdays) {
    var d = new Date();
    d.setTime(d.getTime() + (exdays * 24 * 60 * 60 * 1000));
    var expires = "expires="+d.toUTCString();
    document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
}

function $_GET(param) {
	var vars = {};
	window.location.href.replace( location.hash, '' ).replace(
		/[?&]+([^=&]+)=?([^&]*)?/gi, // regexp
		function( m, key, value ) { // callback
			vars[key] = value !== undefined ? value : '';
		}
	);

	if ( param ) {
		return vars[param] ? vars[param] : null;
	}
	return vars;
}

var th = ['','Thousand','Million', 'Billion','Trillion'];

var dg = ['Zero','One','Two','Three','Four', 'Five','Six','Seven','Eight','Nine'];
var tn = ['Ten','Eleven','Twelve','Thirteen', 'Fourteen','Fifteen','Sixteen', 'Seventeen','Eighteen','Nineteen'];
var tw = ['Twenty','Thirty','Forty','Fifty', 'Sixty','Seventy','Eighty','Ninety'];
var ng = ['0','1','2','3','4','5','6','7','8','9'];

function toWords(s){
    s = s.toString();
    s = s.replace(/[\, ]/g,'');
    if (s != parseFloat(s)) return '';
    var x = s.indexOf('.'); if (x == -1) x = s.length;
    if (x > 15) return 'too big';
    var n = s.split('');
    var str = ''; var sk = 0;
    var    str2 = '';
    var point = '0';
    for (var i=0; i < x; i++) {
        if ((x-i)%3==2) {
            if (n[i] == '1') {
                str += tn[Number(n[i+1])] + ' '; i++;
                sk=1;
            }
            else if (n[i]!=0) {
                str += tw[n[i]-2] + ' ';
                sk=1;
            }
        }
        else if (n[i]!=0) {
            str += dg[n[i]] +' ';
            if ((x-i)%3==0) str += 'Hundred '; sk=1;
        }
            if ((x-i)%3==1) {
                if (sk) str += th[(x-i-1)/3] + ' ';sk=0;
            }
    }
    if (x != s.length) {
        var y = s.length;
        for (var i=x+1; i<y; i++) str2 += ng[n[i]];
    }
    if (y === undefined) {
        str = str + 'Pesos Only';
    }
    else {
        str = str + 'Pesos';
        if (n[y-1] == "." || str2 === "0" || str2 === "00" || str2 === "000" || str2 === "0000") {
            str2 = 'Only';
        }
        else {
            str2 = 'and ' + str2 + '/100 Only';
        }
        if(str2 === 0 ) {

        }
        str = str +' '+ str2;
    }
    return str.replace(/\s+/g,' ');
}