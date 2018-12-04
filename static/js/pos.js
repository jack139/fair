var item_list=[];
var cart_list=[];
var retJson=null;

function keyPress(id)
{
	if ($(id).val()=="") checkOut(); 
	else setTimeout(addItem, 200);
}

function initAll(item)
{
	$.each(item_list, function(i, item){
		$(item+"_tr").remove();		
	});
	item_list=[];
	cart_list=[];
	$("#order_id").html("");
	$("#count_id").html("0");
	$("#total_price").html(parseFloat("0").toFixed(2));
	$("#ft_total").remove();
	$("#ft_discount").remove();
	$("#ft_due").remove();
	$("#ft_paid").remove();
	$("#ft_change").remove();
	$("#item_list").show();
	$("#foot_list").show();
	$("#checkout_div").show();
	$("#pay_div").hide();
	$("#paid_div").hide();

	$("#product_id").prop('disabled', false);
	$("#product_id").val("");
	$("#product_id").focus();
}


function delItem(item)
{
	$("#total_price").html( (parseFloat($("#total_price").html())-parseFloat($(item+"_price").html())).toFixed(2) );
	$(item+"_tr").remove();
	item_list.splice(item_list.indexOf(item),1);
	$("#count_id").html(item_list.length);
	if (item_list.length==0)
		$("#item_list").show();
}

function showData(item)
{
	var rand_id = item["product_id"] + "_" + Math.floor(Math.random()*1000000);
	var shop_row = $("<tr id='"+rand_id+"_tr'>" + 
		"<td><div id='"+rand_id+"_id'>"+item["product_id"]+"</div></td>" +
		"<td id='"+item["product_id"]+"'>"+item["name"]+"</td>" +
		"<td>"+((item["product_id"][2]==1)?"整进整出":((item["product_id"][2]==2)?"散进散出":"散进整出"))+"</td>" +
		"<td><div id='"+rand_id+"_unit_price'>"+item["price"]+"</td>" +
		"<td>"+item["unit_name"]+"</td>" +
		"<td><div id='"+rand_id+"_num'>"+item["weight"]+"</div></td>" +
		"<td><div id='"+rand_id+"_price'>"+item["weight_price"]+"</div></td>" +
		"<td><a class=\"abtn\" href='#' id='"+rand_id+"' " +
		"onclick=\"delItem('#"+rand_id+"');\">删除</a></td></tr>");
	$("#item_list").hide();
	$("#item_list").after(shop_row);
	$("#total_price").html( (parseFloat($("#total_price").html())+parseFloat(item["weight_price"])).toFixed(2) );

	item_list.push("#"+rand_id);
	$("#count_id").html(item_list.length);

	$("#product_id").val("");
	$("#product_id").focus();
}

function addItem()
{
	var product_id=$("#product_id").val();
	var weight=0;

	$.ajax({
		type: "POST",
		url: "/pos/pos_product_id",
		async: true,
		timeout: 15000,
		data: {product_id:product_id},
		dataType: "json",
		complete: function(xhr, textStatus)
		{
			if(xhr.status==200)
			{
				var retJson = JSON.parse(xhr.responseText);
				if (retJson["ret"]==0){
					//showData(retJson["data"]);
					product_id = retJson["data"]["product_id"];
					$("#product_id").val(product_id);

					if (product_id[0]!="w" && product_id[2]=="2"){
						r = alertify.prompt("称重重量：", "", 
							function (e, str1) {
								if (str1==null || str1==""){
									alertify.warning("请输入重量！");
								}
								else {
									weight = parseFloat(str1);
									if (isNaN(weight))
										alertify.warning("请输入数字！");
									else if (weight>0 && weight<20)
										doAddItem(product_id, weight);
									else
										alertify.warning("重量必须大于0，或者小于20！");
								}
							}
						);
					}
					else{
						doAddItem(product_id, 0);
					}

				}
				else {
					alertify.error("商品id错误："+retJson["msg"]);
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
	
function doAddItem(product_id, weight)
{
	if (product_id[0]=="w" && $("#"+product_id).length>0){
		alertify.warning("称重商品不能重复添加！");
		$("#product_id").select();
		return false;
	}
	
	$.ajax({
		type: "POST",
		url: "/pos/pos_json",
		async: true,
		timeout: 15000,
		data: {product_id:product_id, weight:weight},
		dataType: "json",
		complete: function(xhr, textStatus)
		{
			if(xhr.status==200)
			{
				var retJson = JSON.parse(xhr.responseText);
				if (retJson["ret"]==0){
					showData(retJson["data"]);
				}
				else {
					alertify.error("添加商品失败："+retJson["msg"]);
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

function showFoot(id, title, value)
{
	var foot_row = "<tr id=\""+ id +"\"class=\"even\"><td colspan=\"5\"></td>" +
		"<td>" + title + "</td><td class=\"name\">" + value + "</td><td>&nbsp;</td></tr>"
	$("#foot_list").before(foot_row);
}

function showCheckOutResult(data)
{
	if (data['cart_num']!=$("a.abtn").size()){
		alertify.error("实际结算商品数与提交数量不同，请联系管理员！");
		return false;
	}


	$("#foot_list").hide();
	showFoot("ft_total", "价格总计", data["total"]);
	showFoot("ft_discount", "优惠", data["discount"]);
	showFoot("ft_due", "应付总计", data["due"]);

	$("#product_id").prop('disabled', true);
	$("a.abtn").hide();
	$("#order_id").html(""+data['order_id']);
	$("#checkout_div").hide();
	$("#pay_div").show();
	$("#pay_num").val(data['due']).show().focus();
}

function checkOut()
{
	var btn_list=$("a.abtn");

	if (btn_list.size()==0){
		alertify.warning("请添加商品！");
		return false;
	}

	var cart="[";
	$.each(btn_list, function(i, item){
		var rand_id = item.id;
		var product_id = $("#"+rand_id+"_id").html();
		var num = $("#"+rand_id+"_num").html();
		var price = $("#"+rand_id+"_price").html();
		var unit_price = $("#"+rand_id+"_unit_price").html();
		var name = $("#"+product_id).html();

		if (i>0) cart += ",";
		cart += "[\""+product_id+"\",\""+num+"\",\""+price+"\",\""+name+"\"]";

		cart_list.push([product_id, num, price, name, unit_price]);
	});
	cart += "]";

	//alertify.error(cart);

	$.ajax({
		type: "POST",
		url: "/pos/pos_checkout",
		async: true,
		timeout: 15000,
		data: {cart:cart},
		dataType: "json",
		complete: function(xhr, textStatus)
		{
			if(xhr.status==200)
			{
				var retJson = JSON.parse(xhr.responseText);
				if (retJson["ret"]==0){
					showCheckOutResult(retJson["data"]);
				}
				else {
					alertify.error("结算失败："+retJson["msg"]);
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

function doPay()
{
	var order=$("#order_id").html();
	var pay=parseFloat($("#pay_num").val());

	if (isNaN(pay)){
		alertify.warning("请输入数字！");
		return false;
	}

	$.ajax({
		type: "POST",
		url: "/pos/pos_pay",
		async: true,
		timeout: 15000,
		data: {order:order, pay:pay},
		dataType: "json",
		complete: function(xhr, textStatus)
		{
			if(xhr.status==200)
			{
				retJson = JSON.parse(xhr.responseText);
				if (retJson["ret"]==0){
					showFoot("ft_paid", "实际付款", pay.toFixed(2));
					showFoot("ft_change", "找零", retJson["data"]["change"]);
					$("#pay_div").hide();
					$("#paid_div").show();
					if (ableToPrint) print_receipt(retJson["data"]);
					$("#btn_next").focus();
				}
				else {
					alertify.error("付款失败："+retJson["msg"]);
					$("#pay_num").focus();
				}
			}
			else
			{
				alertify.error("网络异常！("+xhr.status+")");
				$("#pay_num").focus();
			}
			
			return false;
		}
	});
	
	return false;

}

function doCancel()
{
	var order=$("#order_id").html();
	
	r = alertify.confirm("确定要取消这次销售吗？", function () {
		$.ajax({
			type: "POST",
			url: "/pos/pos_pay",
			async: true,
			timeout: 15000,
			data: {order:order, pay:'cancel'},
			dataType: "json",
			complete: function(xhr, textStatus)
			{
				if(xhr.status==200)
				{
					var retJson = JSON.parse(xhr.responseText);
					if (retJson["ret"]==0){
						initAll();
						//window.location.href='/pos/pos';
					}
					else {
						alertify.error("付款失败："+retJson["msg"]);
						$("#pay_num").focus();
					}
				}
				else
				{
					alertify.error("网络异常！("+xhr.status+")");
					$("#pay_num").focus();
				}
				
				return false;
			}
		});
	}, function(){});

	return false;

}

function doPrint()
{
	if (retJson!=null){
		if (ableToPrint) print_receipt(retJson["data"]);
		else alertify.warning("未找到打印机，不能打印！");
	}
	else alertify.warning("没有可打印的数据！");
}


function print_receipt(data)
{
	if (notReady()) { return; }

	var order=$("#order_id").html();
	var shop=$("#id_shop_name").html();
	var date=(new Date()).toLocaleString();

	qz.appendHex("x1bx44x0cx13x1ax00"); // 12, 19, 26

	qz.append("U掌柜 <优鲜美味，掌上专柜> urfresh.cn\n\n");
	qz.append("销货单号："+order+"\n");
	qz.append("销货时间："+date+"\n");
	qz.append("================================\n");
	qz.append("商品\x09数量\x09单价\x09金额\n");
	$.each(cart_list, function(i, item){
		if (item[3].length>5)
			qz.append(item[3]+"\n");
		else
    			qz.append(item[3]);
    		qz.append("\x09"+item[1]+"\x09"+item[4]+"\x09"+item[2]+"\n");
	});
	qz.append("================================\n");
	qz.append("合计：\x09\x09\x09"+data["due"]+"\n");
	qz.append("实付：\x09\x09\x09"+data["pay"]+"\n");
	qz.append("找零：\x09\x09\x09"+data["change"]+"\n\n\n\n\n");

	qz.print();
	console.log('print done.');
}

function initPrinter()
{
	findPrinter("lion");
}
