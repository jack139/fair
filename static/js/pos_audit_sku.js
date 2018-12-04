var old_num=null;

function edit_num(id)
{
	old_num = parseInt($("#"+id).html());
	var edit = $("<input id=\""+id+"\" type=\"text\" value=\""+old_num+"\" size=\"5\" onblur=\"update_num('"+id+"')\"/>");
	$("#"+id).replaceWith(edit);
	$("#"+id).focus();
}

function update_num(id)
{
	var sku=$("#sku").val();
	var audit_num=$("#"+id).val();

	if (id[2]=='1' || id[2]=='3')
		f_num = parseInt(audit_num);
	else
		f_num = parseFloat(audit_num);
	if (isNaN(f_num)){
		alertify.warning("请输入数字！"); 
		return false;
	}

	$.ajax({
		type: "POST",
		url: "/pos/audit_sku",
		async: true,
		timeout: 15000,
		data: {product_id:id, audit_num:f_num},
		dataType: "json",
		complete: function(xhr, textStatus)
		{
			if(xhr.status==200)
			{
				var retJson = JSON.parse(xhr.responseText);
				if (retJson["ret"]==0){
					var edit = $("<div id=\""+id+"\" onclick=\"edit_num('"+id+"');\">"+retJson["num"]+"</div>");
					$("#"+id).replaceWith(edit);
				}
				else {
					alertify.error("修改库存失败："+retJson["msg"]);
					var edit = $("<div id=\""+id+"\" onclick=\"edit_num('"+id+"');\">"+old_num+"</div>");
					$("#"+id).replaceWith(edit);
				}
			}
			else
			{
				alertify.error("网络异常！("+xhr.status+")");
				var edit = $("<div id=\""+id+"\" onclick=\"edit_num('"+id+"');\">"+old_num+"</div>");
				$("#"+id).replaceWith(edit);
			}
		}
	});
}

