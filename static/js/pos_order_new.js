var item_list=[];

function keyPress(id)
{
	if ($(id).val()=="") checkOut(); 
	else setTimeout(addItem, 200);
}

function initAll()
{
	$.each(item_list, function(i, item){
		$(item+"_tr").remove();		
	});
	item_list=[];
	$("#item_list").show();

	$("#product_id").prop('disabled', false);
	$("#product_id").val("");
	$("#product_id").focus();
}


function delItem(item)
{
	$(item+"_tr").remove();
	item_list.splice(item_list.indexOf(item),1);
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
		"<td>"+item["unit_name"]+"</td>" +
		"<td id='"+rand_id+"_cost'>"+item["cost_price"]+"</td>" +
		"<td><input type=\"text\" id='"+rand_id+"_num' value=\"\" " + 
		"onkeypress=\"if(event.keyCode==13) $('#product_id').focus();\"/></td>" +
		"<td><a class=\"abtn\" href='#' id='"+rand_id+"' " +
		"onclick=\"delItem('#"+rand_id+"');\">删除</a></td></tr>");
	$("#item_list").hide();
	$("#item_list").after(shop_row);
	
	item_list.push("#"+rand_id);

	$("#product_id").val("");
	$("#"+rand_id+"_num").focus();
}

function addItem()
{
	var product_id=$("#product_id").val();

	if (product_id[0]=="w"){
		alertify.warning("称重商品不能订货！");
		return false;
	}

	if ($("#"+product_id).length>0){
		alertify.warning("该商品已添加，不能重复添加！");
		return false;
	}

	$.ajax({
		type: "POST",
		url: "/pos/pos_json2",
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
					showData(retJson["data"]);
				}
				else {
					alertify.error("查找商品失败："+retJson["msg"]);
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

function checkOut()
{
	r = alertify.confirm("确认提交订货单吗？", function () {
		checkOut2();
	}, function () {});

	return false;
}

function checkOut2()
{
	var btn_list=$("a.abtn");

	if (btn_list.size()==0){
		alertify.warning("请添加商品！");
		return false;
	}

	var cart="[";
	var fail=false;
	$.each(btn_list, function(i, item){
		var rand_id = item.id;
		var product_id = $("#"+rand_id+"_id").html();
		var num = $("#"+rand_id+"_num").val();
		var name = $("#"+product_id).html();
		var cost = $("#"+rand_id+"_cost").html();

		if (isNaN(parseFloat(num))){
			alertify.warning("请输入数字！");
			$("#"+rand_id+"_num").focus();
			fail=true;
			return;
		}

		if (i>0) cart += ",";
		cart += "[\""+product_id+"\",\""+num+"\",\""+name+"\",\""+cost+"\"]";
	});
	cart += "]";

	if (fail) return false;

	//alertify.error(cart);

	$.ajax({
		type: "POST",
		url: "/pos/order_new",
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
					alertify.warning("订货单已成功提交，等待后台处理。");
					initAll();
				}
				else {
					alertify.error("提交失败："+retJson["msg"]);
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
