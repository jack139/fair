
function checkInvent()
{
	var order=$("#id_order2").val();
	var shop=$("#shop_from").val();

	$.ajax({
		type: "POST",
		url: "/stock/order_check_invent",
		async: true,
		timeout: 15000,
		data: {order:order, shop:shop},
		dataType: "json",
		complete: function(xhr, textStatus)
		{
			if(xhr.status==200)
			{
				var retJson = JSON.parse(xhr.responseText);
				if (retJson["ret"]==0){
					$.each(retJson["data"], function(k, v){
						$("#"+k+"_invent").html(v);
					});
				}
				else {
					alertify.error("查找库存失败："+retJson["msg"]);
					$("#product_id").focus();
				}
			}
			else
			{
				alertify.error("网络异常！("+xhr.status+")");
				$("#product_id").focus();
			}
			
			return false;
		}
	});
	
	return false;
}

function checkNum()
{
	var tag_list = $("input.only_4_tag");
	var shop=$("#shop_from").val();
	var success=true;

	if (shop=='-'){
		alertify.warning("请选择发货仓库！");
		return false;
	}

	$.each(tag_list, function(i, item){
		var product_id = item.id;
		var new_num = parseFloat($("#"+product_id).val());
		var invent_num = parseFloat($("#"+product_id+"_invent").html());

		if (isNaN(parseFloat(new_num))){
			alertify.warning("请输入数字！");
			$("#"+rand_id+"_num").focus();
			success=false;
			return;
		}

		/*
		if (new_num>invent_num){
			alertify.warning("商品 " + product_id + " 发货数量不能大于库存数量！");
			success=false;
		}
		*/
	});

	return success;
}

function first()
{
	if (!ableToPrint)
		document.getElementById("qz-status").style.background = "#FFFFFF";
}

function initPrinter()
{
	findPrinter("lion");
}


function doPrint(name)
{
	if (ableToPrint) print_receipt(name);
	else alertify.warning("未找到打印机，不能打印！");
}

function print_receipt(name)
{
	if (notReady()) { return; }

	var date=(new Date()).toLocaleString();
	var list=$("td.only4tag")

	//qz.appendHex("x1bx44x0cx13x1ax00"); // 12, 19, 26

	qz.append("U掌柜 <工单打印> urfresh.cn\n\n");
	qz.append($("#id_order").html()+"\n");
	qz.append($("#id_status").html()+"\n");
	qz.append($("#id_from").html()+"\n");
	qz.append($("#id_to").html()+"\n");
	
	qz.append("================================\n");
	//qz.append("商品\x09数量\x09单价\x09金额\n");
	$.each(list, function(i, item){
		var product_id = item.id;
		qz.append("商品代码："+product_id+"\n");
		qz.append("商品名称："+$("#"+product_id+"_name").html()+"\n");
		qz.append("单位："+$("#"+product_id+"_unit").html()+"\n");
		qz.append("订货数："+$("#"+product_id+"_book").html().trim()+"\n");
		qz.append("发货数："+$("#"+product_id+"_send").html().trim()+"\n");
		qz.append("收货数："+$("#"+product_id+"_recv").html().trim()+"\n");
		qz.append("--------------------------------\n");
    		//qz.append("\x09"+item[1]+"\x09"+item[4]+"\x09"+item[2]+"\n");
	});
	qz.append("********************************\n");
	qz.append("打印地点："+name+"\n");
	qz.append("打印时间："+date+"\n\n\n\n\n\n");

	qz.print();
	console.log('print done.');
}
