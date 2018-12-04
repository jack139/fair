//var min_price=0, max_price=999;

function select_base()
{
	base_sku = $('#base_sku').val();
	if (base_sku=="")
		clearData();
	else
		checkout(base_sku);
}

function check_price()
{
	var price = $('#ref_price').val();
/*
	if (price>max_price){
		alertify.warning("市场价格超出定价范围！");
		$('#price').val(max_price);
		return false;
	}
	else if (price<min_price){
		alertify.warning("市场价格超出定价范围！");
		$('#price').val(min_price);
		return false;
	}
	else{
*/
		if (parseFloat($('#special_price').val())==0)
			$('#special_price').val(price);
		return true;
//	}
}

function check_all()
{
	if ($("#base_sku").val().length==0){
		alertify.warning("请选择sku基础资料！");
		return false;
	}
	if ($("#unit").val().length==0){
		alertify.warning("请选择销售单位！");
		return false;
	}
	
	if  (parseFloat($('#ref_cost').val())<0){
		alertify.warning("成本价格不能小于零！");
		return false;
	}

	//if (!check_price()) return false;
	
	$("#new_sku").submit();
}

function clearData()
{
	$("#sku_name").val("");
	$("#abstract").val("");
	$("#fresh_time").val(0);
	$("#original").val("");
	
	$("#image-list").empty();
}

function showData(data)
{
	//min_price = parseFloat(data["min_price"]);
	//max_price = parseFloat(data["max_price"]);
	
	$("#sku_name").val(data["name"]);
	if ($("#app_title").val()=="") $("#app_title").val(data["name"]);
	$("#abstract").val(data["abstract"]);
	$("#fresh_time").val(data["fresh_time"]);
	$("#original").val(data["original"]);
	//$("#min_price").html(data["min_price"]+" ~ "+data["max_price"]);
	
	$("#image-list").empty();
	
	var list = $("#image-list")[0];
	$.each(data["image"], function(i, item){
		if (item.length>0){
			var li = document.createElement("li"),
			    img = document.createElement("img");
			img.src = "/static/image/product/"+item.substr(0,2)+"/"+item;
			li.appendChild(img);
			list.appendChild(li);
		}
	});
}

function checkout(base_sku)
{
	$.ajax({
		type: "POST",
		url: "/plat/base_sku_json",
		async: true,
		timeout: 15000,
		data: {base_sku:base_sku},
		dataType: "json",
		complete: function(xhr, textStatus)
		{
			if(xhr.status==200)
			{
				var retJson = JSON.parse(xhr.responseText);
				if (retJson["ret"]==0){
					showData(retJson);
				}
				else {
					alertify.error("查询基础资料失败："+retJson["msg"]);
				}
			}
			else
			{
				alertify.error("网络异常！("+xhr.status+")");
			}
		}
	});
}

