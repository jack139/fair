
function checkOut()
{
	r = alertify.confirm("确认提交订货单吗？", function () {
		checkOut2();
	}, function (){});

	return false;
}

function checkOut2()
{
	var btn_list=$("input.only4list");

	if (btn_list.size()==0){
		alertify.warning("没有商品库存！");
		return false;
	}

	var cart="[";
	var fail=false;
	var cc=0;
	$.each(btn_list, function(i, item){
		var product_id = item.id;
		var num = $("#"+product_id).val();
		var name = $("#"+product_id+"_name").html();
		var cost = $("#"+product_id+"_cost").html();

		if (num.trim()=="") return;

		if (isNaN(parseFloat(num))){
			alertify.warning("请输入数字！");
			$("#"+product_id).focus();
			fail=true;
			return;
		}

		if (parseFloat(num)==0) return;

		if (cc>0) cart += ",";
		cc = cc + 1;
		cart += "[\""+product_id+"\",\""+num+"\",\""+name+"\",\""+cost+"\"]";
	});
	cart += "]";

	if (fail) return false;

	if (cart=="[]"){
		alertify.warning("没有任何订货！");
		return false;
	}

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
					//initAll();
					location.href="/pos/order";
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
