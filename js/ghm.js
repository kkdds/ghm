var ctrl_adhead='http://192.168.1.';//working
var ctrl_addr='http://192.168.1.105:9001/sta';
var Gcaitime=5;
var Gvname=0;
var Gpcai='NA';
var Gscly=0;
var Gshowtype='10';
var ektime;
var shell_sta=0;
var ws=null;
var ttfinck=0;
var guolupower=0;
var ifact=0;
var retry=0;
var tdiff=0;
var running_sta=0;
///////////////control///////////////////
$(document).ready(function(){

	$.ajaxSetup({timeout: 500});

	$(".men_div").click(function(){
		if(running_sta==1){
			$('#ctinfo').html( "请先停止烹饪" ).show().fadeOut(1000);
			return;
		}

		$('#cai_title').html($(this).children('.selzone').html());

		Gvname=$(this).attr("vname");
		Gpcai=$(this).attr("bgp");
		Gcaitime=$(this).attr("caitime");
		sec2minsec(Gcaitime);
		Gscly=$(".scr_div").scrollTop();
		$(".mclass_sel").css("background-image","url('"+Gpcai+"')");
		$(".men_div").hide();
		$('.cmendiv').show();
		$.post(ctrl_addr,{m:'sel_cai',cai:Gpcai});
		return false;
	});

	$(".mclass_sel").click(function(){
		if(running_sta==1){
			$('#ctinfo').html( "请先停止烹饪" ).show().fadeOut(1000);
			return;
		}

		$('#cai_title').html("请选择菜品");
		$('.cmendiv').hide();
		$(".mclass_sel").css("background-image","none");
		$(".mclass_sel .men_div").show();
		Gpcai='NA';
		return false;
	});

	$("#addtimebtn").click(function(){
		if(running_sta!=1){return false;}
		$.post(ctrl_addr,{m:'addtime',d:30});
	});

	$("#dectimebtn").click(function(){
		if(running_sta!=1){return false;}
		if(tdiff<33){return false;}
		$.post(ctrl_addr,{m:'addtime',d:-30});
	});
/*
	$(".popBottom").on('click',function(event) {
		event.preventDefault();
		$(".pop").fadeOut();
	});
*/
	$("#div_btn_stop").click(function(){
		$('#div_btn_stop').addClass('ctrl-div-on');
		$.post(ctrl_addr,{m:'gpiooff',d:'zq'});
	});

	$("#div_btn_zq").click(function(){
		if(guolupower==0){$("#ctinfo").html("请先开启电源").show().fadeOut(1000);return;}
		if(shell_sta==1){$("#ctinfo").html("请等待锅盖动作完成").show().fadeOut(1000);return;}
		if(running_sta==1){$("#ctinfo").html("正在烹饪中").show().fadeOut(1500);return;}
		if(shell_sta==0){
			$('audio').attr('src','../voice/qzyggjjhs.mp3');
			myaudio.play();
		}
		//$('#div_btn_zq').addClass('ctrl-div-on');
		$('#div_btn_stop').removeClass('ctrl-div-on');
		$.post(ctrl_addr,{m:'shell',d:'dw',dltime:parseInt(Gcaitime)});
	});

	$("#myonoffswitch").click(function(){
		var md='gpiooff';
		if($("#myonoffswitch").prop("checked")){md='gpioon';}
		$.post(ctrl_addr,{m:md,d:'dy'});
	});

	$("[name='radio']").click(function(){
		if(ifact==0){
			ifact=1;
			ctrl_addr=ctrl_adhead+$(this).attr('net')+':9001/sta';
			$('#ctinfo').html( "选择了 "+$(this).next().text() ).show().fadeOut(1000);
			$('#overlay').show();

			sec2minsec(0);
			$('#cai_title').html("请选择食材");
			$('.cmendiv').hide();
			$(".mclass_sel").css("background-image","none");
			$(".mclass_sel .men_div").show();

			getSta();
		}
	});
});
function getSta(){
	clearInterval(ws);
	$.post(ctrl_addr,{m:'sta'},function(r){
		var rj=r;
		shell_sta=rj.shell_sta;
		ttfinck=rj.ttfinck;

		if(rj.guolupower==1){
			guolupower=1;
			$("#myonoffswitch").prop("checked",true);
		}else{
			guolupower=0;
			$("#myonoffswitch").prop("checked",false);
		}

		if(rj.running_sta==1){
			tdiff=-rj.timediff;
			sec2minsec(tdiff);
			$('#div_btn_zq').addClass('ctrl-div-on');
		}else{
			$('#div_btn_zq').removeClass('ctrl-div-on');
		}
		running_sta=rj.running_sta;

		tempture1=rj.tmp1;
		$("#tmp1").text(tempture1.toFixed(1));

		Gpcai=rj.cai;
		if(Gpcai!='NA'){
			$(".mclass_sel").css("background-image","url('"+Gpcai+"')");
			$(".men_div").hide();
			$('.cmendiv').show();
		}

		$('#overlay').hide();

		ws=setInterval("getSta()", 1000);
		ifact=0;
		retry=0;

	}).error(function(XMLHttpRequest, textStatus, errorThrown){
		if(textStatus=='timeout'){
			$('#overlay').show();
			clearInterval(ws);
			$('#ctinfo').html( "网络未连接" ).show().fadeOut(1500);
		}
		//
		ifact=0;
		retry=retry+1;
		if(retry<15){
			getSta();
		}else{
		}
	});
}
///////////////timer///////////////////
function sec2minsec(ti){
	intDiff=parseInt(ti);
	minute = Math.floor(intDiff / 60);
	second = Math.floor(intDiff) - (minute * 60);
	if (minute <= 9) minute = '0' + minute;
	if (second <= 9) second = '0' + second;
	$('#minute_show').html(minute);
	$('#second_show').html(second);
}
function sec2hourmin(ti){
	intDiff=parseInt(ti);
	minute = Math.floor(intDiff / 3600) ;
	second = Math.floor(intDiff / 60) - (minute * 60);
	if (minute <= 9) minute = '0' + minute;
	if (second <= 9) second = '0' + second;
	$('#hour_wt').html(minute);
	$('#minute_wt').html(second);
}
