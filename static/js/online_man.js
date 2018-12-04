var m_dots = "..";
var id_list = null;
var status_list = null;
var order_list = {};

function doFirst()
{
	if (!ableToPrint)
		document.getElementById("qz-status").style.background = "#FFFFFF";
	showTips("查询事件 "+m_dots);
	setTimeout(checkout, 500);
}

function showTips(strTips)
{
	$('#tips').html(strTips);
}

function flashID(list)
{
	var new_list=[], new_status={};

	$.each(list, function(i, item){new_list[i]=item["id"]; new_status[item["id"]]=item["status"]});
	if (id_list!=null){ 
		$.each(id_list, function(i, item){
			if (new_list.indexOf(item)==-1)
				$("#"+item).remove();
			else if (status_list[item]!=new_status[item])
				$("#"+item).remove();
		});
	}
	id_list=new_list;
	status_list=new_status;
}

/* 拣货 */
function pick_pack(order_id, pick_ok)
{
	//print_label(order_id);
	//return false;

	var runner=$("#runner_"+order_id).val();

	$.ajax({
		type: "POST",
		url: "/online/order_pick",
		async: true,
		timeout: 15000,
		data: {order_id:order_id, ok:((pick_ok)?1:0), runner:runner},
		dataType: "json",
		complete: function(xhr, textStatus)
		{
			if(xhr.status == 403)
			{
				showTips("网络异常！(403)");
			}
			else if(xhr.status==200)
			{
				var retJson = JSON.parse(xhr.responseText);
				if (retJson["ret"]==0){
					if (pick_ok) print_label(order_id);
					$("#"+retJson["id"]).remove();
				}
				else {
					if (m_dots.length>20) m_dots = ".";
					showTips("提交失败： "+retJson["msg"]);
				}
			}
			else
			{
				showTips("网络异常！("+xhr.status+")");
			}
		}
	});
	
	return false;
}


/* 开始派送 */
function to_dispatch(id)
{
	$.ajax({
		type: "POST",
		url: "/online/order_dispatch",
		async: true,
		timeout: 15000,
		data: {id:id},
		dataType: "json",
		complete: function(xhr, textStatus)
		{
			if(xhr.status == 403)
			{
				showTips("网络异常！(403)");
			}
			else if(xhr.status==200)
			{
				var retJson = JSON.parse(xhr.responseText);
				if (retJson["ret"]==0){
					$("#"+retJson["id"]).remove();
				}
				else {
					if (m_dots.length>20) m_dots = ".";
					showTips("提交失败： "+retJson["msg"]);
				}
			}
			else
			{
				showTips("网络异常！("+xhr.status+")");
			}
		}
	});
	
	return false;
}


function createList(id, data)
{
	var prod_list=$("#list_"+id);

	order_list[data['order_id']]=data;

	$.each(data['data'], function(i, item){
		$("<tr><td>"+item['product_id']+
			"</td><td>"+item['title']+
			"</td><td>"+item['num']+"</td></tr>").appendTo(prod_list);
	});

	var runner = "";
	$.each(data['runner'], function(i, item){
		if (item['uname']==data['data']['runner_to_go'])
			runner += "<option value='"+item['uname']+"' selected='selected'>"+item['full_name']+"</option>";
		else
			runner += "<option value='"+item['uname']+"'>"+item['full_name']+"</option>";
	});

	$("<tr><td>"+data['paid_time']+"</td><td>快递员："+
	  "<select id=\"runner_"+data['order_id']+"\">"+runner+"</select>&nbsp;&nbsp;&nbsp;" +
	  "<input type=\"button\" value=\"拣货完成\" onclick=\"pick_pack('"+data['order_id']+"',true);\" />"+
	  "</td><td><input disabled=\"disabled\" type=\"button\" value=\"部分缺货\" onclick=\"pick_pack('"+data['order_id']+"',false);\" />"+
	  "</td></tr>").appendTo(prod_list);
}

function reprint(id)
{

	$.ajax({
		type: "POST",
		url: "/online/order_detail",
		async: true,
		timeout: 15000,
		data: {id:id},
		dataType: "json",
		complete: function(xhr, textStatus)
		{
			if(xhr.status == 403)
			{
				showTips("网络异常！(403)");
			}
			else if(xhr.status==200)
			{
				var retJson = JSON.parse(xhr.responseText);
				if (retJson["num"]>0){
					//showTips("查询到待处理的事件("+ retJson["num"]+'个)');
					//createList(id, retJson);
					order_list[retJson['order_id']]=retJson;
					print_label(retJson['order_id']);
				}
				else if (retJson["num"]==0){
					m_dots += ".";
					if (m_dots.length>10) m_dots = ".";
					showTips("订单中没有商品 "+m_dots);					
				}
				else if (jQuery.isEmptyObject(retJson)){
					showTips("未找到查询结果！");
				}
				else {
					m_dots += ".";
					if (m_dots.length>20) m_dots = ".";
					showTips("查询事件 "+m_dots);
				}
			}
			else
			{
				showTips("网络异常！("+xhr.status+")");
			}
		}
	});
	
	return false;
}


function show_pack(id)
{
	var div_id=$("#"+id);
	var div_pack=$("#pack_"+id);

	if (div_pack.length>0){ /* pack 已经存在 */
		if (div_pack.is(":visible")) div_pack.hide();
		else div_pack.show();
		return false;
	}

	div_id.append($("<div id='pack_"+id+"'></div>"));
	div_pack=$("#pack_"+id);
	div_pack.append($("<table class=\"props_tb\"><thead><tr class=\"even\">" +
		"<th>商品ID</th><th>品名</th><th>数量</th></tr></thead>" +
		"<tbody id=\"list_"+id+"\"></tbody></table><br/>"));

	$.ajax({
		type: "POST",
		url: "/online/order_detail",
		async: true,
		timeout: 15000,
		data: {id:id},
		dataType: "json",
		complete: function(xhr, textStatus)
		{
			if(xhr.status == 403)
			{
				showTips("网络异常！(403)");
			}
			else if(xhr.status==200)
			{
				var retJson = JSON.parse(xhr.responseText);
				if (retJson["num"]>0){
					//showTips("查询到待处理的事件("+ retJson["num"]+'个)');
					createList(id, retJson);
				}
				else if (retJson["num"]==0){
					m_dots += ".";
					if (m_dots.length>10) m_dots = ".";
					showTips("订单中没有商品 "+m_dots);					
				}
				else if (jQuery.isEmptyObject(retJson)){
					showTips("未找到查询结果！");
				}
				else {
					m_dots += ".";
					if (m_dots.length>20) m_dots = ".";
					showTips("查询事件 "+m_dots);
				}
			}
			else
			{
				showTips("网络异常！("+xhr.status+")");
			}
		}
	});
	
	return false;
}

function createImage(list)
{
	$.each(list, function(i, item){
		if ($("#"+item["id"]).length>0){
			var remove=false;
			exist = $("#"+item["id"]).parent()[0]['id']
			switch(item["status"]){
			case "PAID":
				if (exist!="wait_pack") remove=true;
				break;

			case "DISPATCH":
				if (exist!="wait_dispatch") remove=true;
				break;

			default:
				if (item["man"]==1){
					if (exist!="wait_status") remove=true;
				}
				else{
					if (exist!="wait_auto") remove=true;
				}
				break;
			}
			if (remove)
				$("#"+item["id"]).remove();
			else
				return;
		}

		switch(item["status"]){
		case "PAID":
			var image = $("<div id=\""+item["id"]+"\">" +
				"<div><a class='abtn' href='#' onclick=\"return show_pack('"+item["id"]+"');\" >拣货</a>" +
				"&nbsp;" + item['orderNo'] + "&nbsp;-&nbsp;" + item['status'] + 
				"&nbsp;-&nbsp;"  + item['comment'] +
				"&nbsp;付款时间：" + item["paid_time"] +"</div></div>");
			image.appendTo(($("#wait_pack")));
			break;
		case "DISPATCH":
			var image = $("<div id=\""+item["id"]+"\">" +
				"<a class='abtn' href='#' onclick=\"return to_dispatch('"+item["id"]+"');\" >开始派送</a>" +
				"&nbsp;" + item['orderNo'] + "&nbsp;-&nbsp;" + item['status'] + 
				"&nbsp;-&nbsp;快递员：" + item['runner']['name'] + "(" + item['runner']['tel'] + ")" +
				"&nbsp;-&nbsp;"  + item['comment'] + 
				"<a class='abtn' href='#' onclick=\"return reprint('"+item["id"]+"');\" >补打面单</a>"  + 
				"&nbsp;付款时间：" + item["paid_time"] +"</div>");
			image.appendTo(($("#wait_dispatch")));
			break;
		default:
			if (item["man"]==1){
				var image = $("<div id=\""+item["id"]+"\">" +
					"<a class='abtn' href='/view_event?todo="+item["orderNo"]+"' target='_blank'>人工处理</a>" +
					"&nbsp;" + item['orderNo'] + "&nbsp;-&nbsp;" + item['status'] + 
					"&nbsp;-&nbsp;"  + item['comment']  + 
					"&nbsp;付款时间：" + item["paid_time"] +"</div>");
				image.appendTo(($("#wait_status")));
			} 
			else{
				var image = $("<div id=\""+item["id"]+"\">" +
					"<a class='abtn' href='/view_event?todo="+item["orderNo"]+"' target='_blank'>查看详情</a>" +
					"&nbsp;" + item['orderNo'] + "&nbsp;-&nbsp;" + item['status'] + 
					"&nbsp;-&nbsp;"  + item['comment'] +
					"&nbsp;付款时间：" + item["paid_time"] + "</div>");
				image.appendTo(($("#wait_auto")));
			}
			break;
		}

	});
}

function checkout()
{
	$.ajax({
		type: "POST",
		url: "/online/order_check",
		async: true,
		timeout: 15000,
		data: {},
		dataType: "json",
		complete: function(xhr, textStatus)
		{
			if(xhr.status == 403)
			{
				showTips("网络异常！(403)");
			}
			else if(xhr.status==200)
			{
				var retJson = JSON.parse(xhr.responseText);
				if (retJson["num"]>0){
					showTips("查询到待处理的事件("+ retJson["num"]+'个)');
					flashID(retJson["data"]);
					createImage(retJson["data"]);
				}
				else if (retJson["num"]==0){
					flashID([]);
					m_dots += ".";
					if (m_dots.length>10) m_dots = ".";
					showTips("没有需处理的事件 "+m_dots);					
				}
				else if (jQuery.isEmptyObject(retJson)){
					showTips("未找到查询结果！");
				}
				else {
					m_dots += ".";
					if (m_dots.length>20) m_dots = ".";
					showTips("查询事件 "+m_dots);
				}
			}
			else
			{
				showTips("网络异常！("+xhr.status+")");
			}
		}
	});

	console.log('refresh');

	if (pt_shop)
		setTimeout(checkout, 10000);
	else
		setTimeout(checkout, 5000);
}

/* 打印标签 */
function print_label(order_id)
{
	if (notReady()) { return; }

	var date=(new Date()).toLocaleString();

	if ($("input[type='radio'][name='paper_type']:checked").val()=="receipt_paper"){
		var text = [];
		var text2 = [];
		var line1=0, line2=0;

		text[line1++]=" ";
		text[line1++]="订单号："+order_id+" 发货站："+order_list[order_id]['shop'];
		text[line1++]="收货人："+order_list[order_id]['address'][1];
		text[line1++]="电话："+order_list[order_id]['address'][2];
		text[line1++]="收货地址：";
		if (order_list[order_id]['address'][3].length>44){
			text[line1++]=order_list[order_id]['address'][3].substring(0,22);
			text[line1++]=order_list[order_id]['address'][3].substring(22,44);
			text[line1++]=order_list[order_id]['address'][3].substring(44);
		} else if (order_list[order_id]['address'][3].length>22){
			text[line1++]=order_list[order_id]['address'][3].substring(0,22);
			text[line1++]=order_list[order_id]['address'][3].substring(22);
		} else {
			text[line1++]=order_list[order_id]['address'][3];
		}
		text[line1++]="下单时间："+order_list[order_id]['paid_time'];
		text[line1++]=" ";
		text[line1++]="商品清单：";

		var total=0;
		$.each(order_list[order_id]['data'], function(i, item){
			var text0 = item['title']+"~"+item['num']
			total += item['num'];　
			if (text0.length>22){
				text[line1++]=""+(i+1)+"."+text0.substring(0,22);
				text[line1++]="  "+text0.substring(22);
			}else{
				text[line1++]=""+(i+1)+"."+text0;
			}
		});
		text[line1++]="实付金额："+order_list[order_id]['due']+"  数量合计："+total;
		text[line1++]=" ";
		text[line1++]="     *********** 用户留言 ***********";

		if (order_list[order_id]['user_note'].length>22){
			text[line1++]=order_list[order_id]['user_note'].substring(0,22);
			text[line1++]=order_list[order_id]['user_note'].substring(22);
		}else{
			text[line1++]=order_list[order_id]['user_note'];
		}

		text[line1++]=" ";
		text[line1++]="-----------------------------------------------";
		text[line1++]=" ";

		text2[line2++]="订单号："+order_id+"  发货站："+order_list[order_id]['shop'];
		text2[line2++]="收货人："+order_list[order_id]['address'][1];
		text2[line2++]="电话："+order_list[order_id]['address'][2];
		text2[line2++]=" ";
		text2[line2++]="收货人签名：";
		text2[line2++]=" ";
		text2[line2++]=" ";

		var header=120;
		var list_height = parseInt(((line1+line2)*30+200+header)/8);

		qz.append("SIZE 74 mm," + list_height + " mm\n" + 
			"GAP 0,0\n" +
			"REFERENCE 0,0\n" +
			"SPEED 4.0\n" +
			"DENSITY 8\n" +
			"SET PEEL OFF\n" +
			"SET CUTTER OFF\n" +
			"SET PARTIAL_CUTTER OFF\n" +
			"SET TEAR ON\n" +
			"DIRECTION 0\n" +
			"SHIFT 0\n" +
			"OFFSET 0 mm\n" +
			"CLS\n");

		qz.append("TEXT 210,30,\"TSS24.BF2\",0,2,2,\"U掌柜\"\n");
		qz.append("TEXT 150,90,\"TSS24.BF2\",0,1,1,\"<优鲜美味，掌上专柜>\"\n");
		qz.append("TEXT 210,120,\"TSS24.BF2\",0,1,1,\"urfresh.cn\"\n");

		$.each(text, function(i, item){
			qz.append("TEXT 25,"+(header+30+i*30)+",\"TSS24.BF2\",0,1,1,\""+item+"\"\n");
		});

		qz.append("BARCODE 10,"+(header+30+line1*30)+",\"128\",80,0,0,3,7,\""+order_id+"\"\n");

		$.each(text2, function(i, item){
			qz.append("TEXT 25,"+(header+30+line1*30+100+i*30)+",\"TSS24.BF2\",0,1,1,\""+item+"\"\n");
		});

		qz.append("PRINT 1,1\n" + "EOP\n");
		qz.print();

	} else if (pt_shop==false) {
		qz.append("SIZE 74 mm,80 mm\n" + 
			"GAP 3 mm,0 mm\n" +
			"REFERENCE 0,0\n" +
			"SPEED 4.0\n" +
			"DENSITY 8\n" +
			"SET PEEL OFF\n" +
			"SET CUTTER OFF\n" +
			"SET PARTIAL_CUTTER OFF\n" +
			"SET TEAR ON\n" +
			"DIRECTION 0\n" +
			"SHIFT 0\n" +
			"OFFSET 0 mm\n" +
			"CLS\n");

		//qz.append("TEXT 30,30,\"TSS24.BF2\",0,1,1,\"订单号："+order_id+"\"\n");
		qz.append("TEXT 300,30,\"TSS24.BF2\",0,1,1,\"发货站："+order_list[order_id]['shop']+"\"\n");
		qz.append("TEXT 30,60,\"TSS24.BF2\",0,1,1,\"收货人："+order_list[order_id]['address'][1]+"\"\n");
		qz.append("TEXT 30,90,\"TSS24.BF2\",0,1,1,\"电话："+order_list[order_id]['address'][2]+"\"\n");
		qz.append("TEXT 30,120,\"TSS24.BF2\",0,1,1,\""+order_list[order_id]['address'][3].substring(0,20)+"\"\n");
		qz.append("TEXT 30,150,\"TSS24.BF2\",0,1,1,\""+order_list[order_id]['address'][3].substring(20)+"\"\n");

		qz.append("TEXT 30,200,\"TSS24.BF2\",0,1,1,\"U掌柜 <优鲜美味，掌上专柜> urfresh.cn\"\n");


		qz.append("TEXT 30,270,\"TSS24.BF2\",0,1,1,\"订单号："+order_id+"\"\n");
		qz.append("TEXT 30,310,\"TSS24.BF2\",0,1,1,\"收货人："+order_list[order_id]['address'][1]+"\"\n");
		qz.append("TEXT 300,310,\"TSS24.BF2\",0,1,1,\"发货站："+order_list[order_id]['shop']+"\"\n");
		qz.append("TEXT 30,350,\"TSS24.BF2\",0,1,1,\"电话："+order_list[order_id]['address'][2]+"\"\n");
		qz.append("TEXT 30,390,\"TSS24.BF2\",0,1,1,\""+order_list[order_id]['address'][3].substring(0,20)+"\"\n");
		qz.append("TEXT 30,430,\"TSS24.BF2\",0,1,1,\""+order_list[order_id]['address'][3].substring(20)+"\"\n");

		//qz.append("BARCODE 30,480,\"128M\",80,0,0,4,12,\"!104" + 
		//	order_id[0]+"!099"+order_id.substring(1)+"\"\n");
		qz.append("BARCODE 10,480,\"128\",80,0,0,3,7,\""+order_id+"\"\n");
		qz.append("TEXT 300,580,\"TSS24.BF2\",0,1,1,\"收货人签名："+"\"\n");
		qz.append("TEXT 30,610,\"TSS24.BF2\",0,1,1,\""+order_list[order_id]['paid_time']+"\"\n");

		qz.append("PRINT 1,1\n" + "EOP\n");
		qz.print();

		//var list_size = order_list[order_id]['data'].length*30;

		qz.append("SIZE 74 mm,80 mm\n" + 
			"GAP 3 mm,0 mm\n" +
			"REFERENCE 0,0\n" +
			"SPEED 4.0\n" +
			"DENSITY 8\n" +
			"SET PEEL OFF\n" +
			"SET CUTTER OFF\n" +
			"SET PARTIAL_CUTTER OFF\n" +
			"SET TEAR ON\n" +
			"DIRECTION 0\n" +
			"SHIFT 0\n" +
			"OFFSET 0 mm\n" +
			"CLS\n");	
		//qz.append("TEXT 25,30,\"TSS24.BF2\",0,1,1,\"订单号："+order_id+"\"\n");

		var total=0;
		var line=0;
		$.each(order_list[order_id]['data'], function(i, item){
			var text0 = item['title']+"~"+item['num']
			total += item['num'];
			if (text0.length>20){
				qz.append("TEXT 25,"+(70+line*30)+",\"TSS24.BF2\",0,1,1,\""+(i+1)+"."+text0.substring(0,22)+"\"\n");
				line++;
				qz.append("TEXT 25,"+(70+line*30)+",\"TSS24.BF2\",0,1,1,\""+"   "+text0.substring(22)+"\"\n");
			}else{
				qz.append("TEXT 25,"+(70+line*30)+",\"TSS24.BF2\",0,1,1,\""+(i+1)+"."+text0+"\"\n");
			}
			line++;
		});

		qz.append("TEXT 300,30,\"TSS24.BF2\",0,1,1,\"总数量："+total+"\"\n");

		qz.append("PRINT 1,1\n" + "EOP\n");
		qz.print();
	} else {
		/* 拼团标签打印 */

		var text = [];
		var line1 = 0;

		text[line1++]=" ";
		text[line1++]="订单号："+order_id;
		text[line1++]="发货站："+order_list[order_id]['shop'];
		text[line1++]="收货人："+order_list[order_id]['address'][1];
		text[line1++]="电话："+order_list[order_id]['address'][2];
		text[line1++]="收货地址：";
		if (order_list[order_id]['address'][3].length>40){
			text[line1++]=order_list[order_id]['address'][3].substring(0,20);
			text[line1++]=order_list[order_id]['address'][3].substring(20,40);
			text[line1++]=order_list[order_id]['address'][3].substring(40);
		} else if (order_list[order_id]['address'][3].length>20){
			text[line1++]=order_list[order_id]['address'][3].substring(0,20);
			text[line1++]=order_list[order_id]['address'][3].substring(20);
		} else {
			text[line1++]=order_list[order_id]['address'][3];
		}
		text[line1++]="下单时间："+order_list[order_id]['paid_time'];
		text[line1++]=" ";

		var total=0;
		$.each(order_list[order_id]['data'], function(i, item){
			var text0 = item['title']
			if (text0.length>20){
				text[line1++]=text0.substring(0,20);
				text[line1++]=text0.substring(20);
			}else{
				text[line1++]=text0;
			}
		});
		text[line1++]=" ";

		var header=0;

		qz.append("SIZE 100 mm,70 mm\n" + 
			"GAP 3 mm,0 mm\n" +
			"REFERENCE 0,0\n" +
			"SPEED 4.0\n" +
			"DENSITY 8\n" +
			"SET PEEL OFF\n" +
			"SET CUTTER OFF\n" +
			"SET PARTIAL_CUTTER OFF\n" +
			"SET TEAR ON\n" +
			"DIRECTION 0\n" +
			"SHIFT 0\n" +
			"OFFSET 0 mm\n" +
			"CLS\n");

		$.each(text, function(i, item){
			qz.append("TEXT 80,"+(header+30+i*30)+",\"TSS24.BF2\",0,1,1,\""+item+"\"\n");
		});

		qz.append("BARCODE 100,"+(header+30+line1*30)+",\"128\",80,0,0,2,5,\""+order_id+"\"\n");

		//qz.append("TEXT 100,"+(header+30+line1*30+130)+",\"TSS24.BF2\",0,2,2,\""+order_list[order_id]['address'][1]+"\"\n");
		//qz.append("TEXT 100,"+(header+30+line1*30+190)+",\"TSS24.BF2\",0,2,2,\""+order_list[order_id]['address'][2]+"\"\n");

		qz.append("PRINT 1,1\n" + "EOP\n");
		qz.print();

	}
	console.log('print done.');

	return false;
}

function initPrinter()
{
	findPrinter("zebra");
}
