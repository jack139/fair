
function first()
{
	$("#return_price").focus();
}

function check_key()
{
	var weight = parseFloat($('#weight').val());
	var price = parseFloat($('#return_price').val());
	if (isNaN(weight)) { weight = 0.00; }
	if (isNaN(price)) { price = 0.00; }
	var weight_price = price*weight;
	$("#price_show").html(weight_price.toFixed(2));
	//$("#inventory_num").html((inventory_num-weight).toFixed(2));
}
