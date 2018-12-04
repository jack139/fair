var ref_price=0;
var passwd=null;

function doOnline(product_id, online)
{
	$.ajax({
		type: "POST",
		url: "/pos/invent_online",
		async: true,
		timeout: 15000,
		data: {product_id:product_id, online:online},
		dataType: "json",
		complete: function(xhr, textStatus)
		{
			if(xhr.status==200)
			{
				var retJson = JSON.parse(xhr.responseText);
				if (retJson["ret"]==0){
					if (online==1){
						$("#online").html("上架");
					}
					else{
						$("#online").html("下架");
					}
					alertify.warning(retJson["msg"]);
				}
				else {
					alertify.error("操作失败："+retJson["msg"]);
				}
			}
			else
			{
				alertify.error("网络异常！("+xhr.status+")");
			}
			
			return false;
		}
	});

}

function onlineON()
{
	var product_id=$("#product_id").html();
	
	r = alertify.confirm("确定要上架吗？", function () {
		doOnline(product_id, 1);
	}, function () {});

	return false;
}

function onlineOFF()
{
	var product_id=$("#product_id").html();
	
	r = alertify.confirm("确定要上架吗？", function () {
		doOnline(product_id, 0);
	}, function () {});

	return false;
}


function edit_price()
{
	var edit = $("<input id=\"price_num\" type=\"text\" value=\"\" size=\"5\" " + 
		"onkeypress=\"if(event.keyCode==13) return update_price();\"/>" +
		"&nbsp;<a class=\"abtn\" href=\"#\" onclick=\"return update_price();\">确定</a>"
		);
	$("#td_edit_price").empty().append(edit);
	$("#price_num").focus();

	return false;
}

function update_price()
{
	var price=$("#price_num").val();
	var product_id=$("#product_id").html();

	if (price==""){
		var edit="<a class=\"abtn\" href=\"#\" onclick=\"return edit_price();\">改门店价格</a>"
		$("#td_edit_price").empty().append(edit);
		return false;
	}

	f_price = parseFloat(price);
	if (isNaN(f_price)){
		alertify.warning("请输入数字！"); return false;
	}
	else if (f_price<=0){
		alertify.warning("价格必须大于0！"); return false;
	}
	else if (f_price>ref_price){
		alertify.warning("价格必须小于参考单价！"); return false;
	}

	r = alertify.confirm("确定要修改价格吗？", 
		function () {
			alertify.prompt('请输入密码：','',
				function(evt, value){
					var passwd = value.trim();

					if (passwd.length>0){
						doUpdatePrice(product_id, f_price, passwd);
					} else {
						alertify.error('请输入密码！');
					}
				}
			).set('type','password');
		},
		function () {
			var edit="<a class=\"abtn\" href=\"#\" onclick=\"return edit_price();\">改门店价格</a>"
			$("#td_edit_price").empty().append(edit);
		}
	);

	return false;
}

function doUpdatePrice(product_id, price, passwd)
{
	$.ajax({
		type: "POST",
		url: "/pos/invent_price",
		async: true,
		timeout: 15000,
		data: {product_id:product_id, type:"price", price:price, passwd:passwd },
		dataType: "json",
		complete: function(xhr, textStatus)
		{
			if(xhr.status==200){
				var retJson = JSON.parse(xhr.responseText);
				if (retJson["ret"]==0){
					alertify.warning(retJson["msg"]);
					var edit="<a class=\"abtn\" href=\"#\" onclick=\"return edit_price();\">改门店价格</a>"
					$("#td_edit_price").empty().append(edit);
					$("#td_price").html(price.toFixed(2)+" 元");
				}
				else {
					alertify.error("修改价格失败："+retJson["msg"]);
					var edit="<a class=\"abtn\" href=\"#\" onclick=\"return edit_price();\">改门店价格</a>"
					$("#td_edit_price").empty().append(edit);
				}
			}
			else{
				alertify.error("网络异常！("+xhr.status+")");
				var edit="<a class=\"abtn\" href=\"#\" onclick=\"return edit_price();\">改门店价格</a>"
				$("#td_edit_price").empty().append(edit);
			}
		}
	});
}

function save_list_in_app()
{

	var list_in_app=$('input[type="radio"][name="list_in_app"]:checked').val();
	var product_id=$("#product_id").html();

	if (list_in_app!='0' && $("#td_image").length==0){
		alertify.error("没有图片，不能上App销售！");
		return false;
	}

	$.ajax({
		type: "POST",
		url: "/pos/invent_price",
		async: true,
		timeout: 15000,
		data: {product_id:product_id, type:"list_in_app", list_in_app:list_in_app },
		dataType: "json",
		complete: function(xhr, textStatus)
		{
			if(xhr.status==200){
				var retJson = JSON.parse(xhr.responseText);
				if (retJson["ret"]==0){
					alertify.warning(retJson["msg"]);
					$("#td_list_in_app").html((list_in_app!='0')?"是":"不是");
				}
				else {
					alertify.error("保存失败："+retJson["msg"]);
				}
			}
			else{
				alertify.error("网络异常！("+xhr.status+")");
			}
		}
	});

	return false;
}

function save_category()
{

	var category=$("#selct_category").val();
	var product_id=$("#product_id").html();

	$.ajax({
		type: "POST",
		url: "/pos/invent_price",
		async: true,
		timeout: 15000,
		data: {product_id:product_id, type:"category", category:category },
		dataType: "json",
		complete: function(xhr, textStatus)
		{
			if(xhr.status==200){
				var retJson = JSON.parse(xhr.responseText);
				if (retJson["ret"]==0){
					alertify.warning(retJson["msg"]);
					$("#td_category").html(jQuery("#selct_category :selected").text());
				}
				else {
					alertify.error("保存失败："+retJson["msg"]);
				}
			}
			else{
				alertify.error("网络异常！("+xhr.status+")");
			}
		}
	});

	return false;
}

function save_sort_weight()
{

	var sort_weight=$("#input_sort_weight").val();
	var product_id=$("#product_id").html();

	i_sort_weight = parseInt(sort_weight);
	if (isNaN(i_sort_weight)){
		alertify.warning("请输入数字！"); return false;
	}

	$.ajax({
		type: "POST",
		url: "/pos/invent_price",
		async: true,
		timeout: 15000,
		data: {product_id:product_id, type:"sort_weight", sort_weight:i_sort_weight },
		dataType: "json",
		complete: function(xhr, textStatus)
		{
			if(xhr.status==200){
				var retJson = JSON.parse(xhr.responseText);
				if (retJson["ret"]==0){
					alertify.warning(retJson["msg"]);
					$("#td_sort_weight").html(i_sort_weight);
				}
				else {
					alertify.error("保存失败："+retJson["msg"]);
				}
			}
			else{
				alertify.error("网络异常！("+xhr.status+")");
			}
		}
	});

	return false;
}

