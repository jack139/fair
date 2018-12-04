var order_list = {};

function doFirst()
{
	if (!ableToPrint)
		document.getElementById("qz-status").style.background = "#FFFFFF";
}

function addLog(strTips)
{
	var image = $("<div>"+strTips+"</div>");
	image.appendTo(($("#action_log")));
}

/* 拣货 */
function pick_pack(order_id, pick_ok)
{

	$.ajax({
		type: "POST",
		url: "/online/order_pick",
		async: true,
		timeout: 15000,
		data: {order_id:order_id, ok:((pick_ok)?1:0), runner:order_list[order_id]['runner_to_go']},
		dataType: "json",
		complete: function(xhr, textStatus)
		{
			if(xhr.status == 403)
			{
				addLog("网络异常！(403) "+order_id);
			}
			else if(xhr.status==200)
			{
				var retJson = JSON.parse(xhr.responseText);
				if (retJson["ret"]==0){
					addLog("提交成功："+order_id);
				}
				else {
					addLog("提交失败："+retJson["msg"]+" "+order_id);
				}
			}
			else
			{
				addLog("网络异常！("+xhr.status+") "+order_id);
			}
		}
	});
	
	return false;
}

function print_all()
{
	var time = 500;

	alertify.confirm("确定要开始批量打印吗？", function () {
		$.each(order_pool, function(i, item){			
			setTimeout( function(){
				reprint(item); // 测试
			}, time)
	      		time += 3000;
		});
	}, function(){}).set('defaultFocus', 'cancel');

	return false;
}

function pick_all()
{
	var time = 500;

	alertify.confirm("将本页面所有订单设置为拣货完成吗？", function () {
		$.each(order_pool, function(i, item){			
			setTimeout( function(){
				pick_pack(item, true);
			}, time)
	      		time += 500;
		});
	}, function(){}).set('defaultFocus', 'cancel');

	return false;
}

function print_single()
{
	var order_id = $("#single_order_id").val();

	if (order_id.length>0)
		reprint(order_id);
	else
		alertify.error("请输入订单号！")

	return false;
}


function reprint(id)
{

	$.ajax({
		type: "POST",
		url: "/online/order_detail",
		async: true,
		timeout: 15000,
		data: {order_id:id},
		dataType: "json",
		complete: function(xhr, textStatus)
		{
			if(xhr.status == 403)
			{
				addLog("网络异常！(403)");
			}
			else if(xhr.status==200)
			{
				var retJson = JSON.parse(xhr.responseText);
				if (retJson["num"]>0){
					order_list[retJson['order_id']]=retJson;
					print_label(retJson['order_id']);
				}
				else if (retJson["num"]==0){
					addLog("订单中没有商品 "+id);	
				}
				else if (jQuery.isEmptyObject(retJson)){
					addLog("未找到查询结果！"+id);
				}
				else {
					addLog("查询事件 "+id);
				}
			}
			else
			{
				addLog("网络异常！("+xhr.status+") "+id);
			}
		}
	});
	
	return false;
}




/* 打印标签 */
function print_label(order_id)
{
	if (notReady()) { return; }

	var date=(new Date()).toLocaleString();

	/* 拼团标签打印 */

	var text = [];
	var line1 = 0;

	text[line1++]=" ";
	text[line1++]="订单号："+order_id;
	text[line1++]="发货站："+order_list[order_id]['shop'];
	text[line1++]="收货人："+order_list[order_id]['address'][1];
	text[line1++]="电话："+order_list[order_id]['address'][2];
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

	var total=0;
	$.each(order_list[order_id]['data'], function(i, item){
		var text0 = item['title']
		if (text0.length>22){
			text[line1++]=text0.substring(0,22);
			text[line1++]=text0.substring(22);
		}else{
			text[line1++]=text0;
		}
	});
	text[line1++]=" ";

	var header=0;

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

	$.each(text, function(i, item){
		qz.append("TEXT 30,"+(header+30+i*30)+",\"TSS24.BF2\",0,1,1,\""+item+"\"\n");
	});

	qz.append("BARCODE 60,500,\"128\",80,0,0,2,5,\""+order_id+"\"\n");

	qz.append("PRINT 1,1\n" + "EOP\n");
	qz.print();

	console.log('print done.');

	return false;
}

function initPrinter()
{
	findPrinter("zebra");
}
