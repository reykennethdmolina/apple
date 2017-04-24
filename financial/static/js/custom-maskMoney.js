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

function initMaskMoney(className){
	$('.' + className).maskMoney({thousands:',', decimal:'.', affixesStay: true});
}

/* Amount to words convertion */
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
		for (var i=0; i < x; i++) {if ((x-i)%3==2)
		{
			if (n[i] == '1') {
			str += tn[Number(n[i+1])] + ' '; i++;
			sk=1;
			} else if (n[i]!=0) {
			str += tw[n[i]-2] + ' ';
			sk=1; }
			} else if (n[i]!=0) {
			str += dg[n[i]] +' ';
			if ((x-i)%3==0) str += 'Hundred '; sk=1;}
			if ((x-i)%3==1) {if (sk) str += th[(x-i-1)/3] + ' ';sk=0;}} if (x != s.length) {
			var y = s.length;

			for (var i=x+1; i<y; i++) str2 += ng[n[i]];
			}
			if (y === undefined) {
			    str = str + 'Pesos Only';
			} else {
			    str = str + 'Pesos';
			    if (n[y-1] == "." || str2 === "0" || str2 === "00" || str2 === "000" || str2 === "0000") {
			        str2 = 'Only';
			    } else {
			        str2 = 'and ' + str2 + '/100 Only';
			    }

			    if(str2 === 0 ) {}
			    str = str +' '+ str2;
		}
	    return str.replace(/\s+/g,' ');
	}

/* End Amount to words convertion */