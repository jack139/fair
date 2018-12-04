var sku=null;
var select_whouse=null;
var old_num=0;
var shop_list={};

function add_shop()
{
	var shop = $("#shop_list").val();
	if (shop==""){
		alertify.warning("请选择站点！");
		return false;
	}

	if ($("#"+shop).length>0){
		alertify.warning("此站点已存在库存！");
		return false;
	}

	//var shop_row = $("<tr><td>"+shop_list[shop]+"</td><td><div id=\""+shop+"\" onclick=\"edit_num('"+shop+"');\">0</div></td></tr>");
	var shop_row = $("<tr><td>"+shop_list[shop]+"</td><td><div id=\""+shop+"\">0</div></td>"
		+ "<td><div id=\"edit_"+shop+"\">"
		+ "<a class=\"abtn\" href=\"#\" onclick=\"return edit_num('"+shop
		+ "');\">补货</a></div></td></tr>");

	$("#invent_col").prop("rowspan", parseInt($("#invent_col").prop("rowspan"))+1);
	$("#invent").after(shop_row);
	return false;
}

function edit_num(id)
{
	old_num = parseInt($("#"+id).html());
	var edit = $("<input id=\"num_"+id+"\" type=\"text\" value=\"0\" size=\"5\" " +
		"onkeypress=\"if(event.keyCode==13) return false;\" onblur=\"update_num('"+id+"')\"/>");
	var select2 = select_whouse.clone().attr("id", "select_"+id);
	$("#edit_"+id).empty().append("从 ").append(select2).append(" 补货 ").append(edit);
	//$("#num_"+id).focus();
	$("#select_"+id).focus();
	return false;
}

function update_num(id)
{
	var num=$("#num_"+id).val();
	var whouse=$("#select_"+id).val();
	var product_id=$("#product_id").html();

	f_num = parseFloat(num);
	if (isNaN(f_num)){
		alertify.warning("请输入数字！"); return false;
	}
	else if (f_num<0){
		alertify.warning("数量必须大于0！"); return false;
	}
	else if (f_num==0){
		var edit = "<a class=\"abtn\" href=\"#\" onclick=\"return edit_num('"+id+"');\">补货</a>";
		$("#edit_"+id).empty().append(edit);
		return false;
	}

	if (whouse==""){
		alertify.warning("请选择发货仓库！");	
		$("#select_"+id).focus();
		return false;
	}

	$.ajax({
		type: "POST",
		url: "/stock/inventory_edit",
		async: true,
		timeout: 15000,
		data: {sku:sku, shop:id, num:num, product_id:product_id, whouse:whouse },
		dataType: "json",
		complete: function(xhr, textStatus)
		{
			if(xhr.status==200){
				var retJson = JSON.parse(xhr.responseText);
				if (retJson["ret"]==0){
					//var edit = $("<div id=\""+id+"\">"+retJson["num"]+"</div>");
					//$("#"+id).replaceWith(edit);
					//$("#total_num").html(parseInt($("#total_num").html())-parseInt(old_num)+parseInt(num));

					alertify.warning(retJson["msg"]);
					var edit = "<a class=\"abtn\" href=\"#\" onclick=\"return edit_num('"+id+"');\">补货</a>";
					$("#edit_"+id).empty().append(edit);

					checkout();
				}
				else {
					alertify.error("修改库存失败："+retJson["msg"]);
					var edit = "<a class=\"abtn\" href=\"#\" onclick=\"return edit_num('"+id+"');\">补货</a>";
					$("#edit_"+id).empty().append(edit);
				}
			}
			else{
				alertify.error("网络异常！("+xhr.status+")");
				var edit = "<a class=\"abtn\" href=\"#\" onclick=\"return edit_num('"+id+"');\">补货</a>";
				$("#edit_"+id).empty().append(edit);
			}
		}
	});
}

function showData(data)
{
	var total_num = 0.0;

	$.each(data, function(key, item){
		var shop_row;
		var num_show = item["num"].toFixed(2);

		total_num += item["num"];

		if (item["num_change"]<0)
			num_show += " －"+Math.abs(item["num_change"]);
		else if (item["num_change"]>0)
			num_show += " ＋"+item["num_change"];

		if ($("#"+item["shop"]).length>0){
			$("#"+item["shop"]).html(num_show);
			return;
		}

		if (shop_list[item["shop"]].indexOf("（仓库）")==-1){
			shop_row = $("<tr><td>"+shop_list[item["shop"]]+"</td><td><div id=\""+item["shop"]+"\">"
				+ num_show+"</div></td>"
				+ "<td><div id=\"edit_"+item["shop"]+"\">"
				+ "<a class=\"abtn\" href=\"#\" onclick=\"return edit_num('"+item["shop"]
				+ "');\">补货</a></div></td></tr>");
		}
		else{
			shop_row = $("<tr><td>"+shop_list[item["shop"]]+"</td><td><div id=\""+item["shop"]
				+ "\">"+num_show+"</div></td><td></td></tr>");
		}
		$("#invent_col").prop("rowspan", parseInt($("#invent_col").prop("rowspan"))+1);
		$("#invent").after(shop_row);
		
		var his_txt=shop_list[item["shop"]]+"\n";
		$.each(item["history"], function(j, jtem){
			his_txt += jtem[0]+"，用户："+jtem[1]+"，操作："+jtem[2]+"\n";
		});
		$("#history").html(his_txt);
	});
	
	$("#total_num").html(total_num.toFixed(2));
}

function checkout(base_sku)
{	
	$.ajax({
		type: "POST",
		url: "/stock/inventory_json",
		async: true,
		timeout: 15000,
		data: {sku:sku},
		dataType: "json",
		complete: function(xhr, textStatus){
			if(xhr.status==200){
				var retJson = JSON.parse(xhr.responseText);
				if (retJson["ret"]==0){
					showData(retJson["data"]);
				}
				else{
					alertify.error("查询库存数据失败："+retJson["msg"]);
				}
			}
			else{
				alertify.error("网络异常！("+xhr.status+")");
			}
		}
	});
}

