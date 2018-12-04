
function share_receive_red_envelope(){
	var num = $("#phone_number").val();
	var patt1 = /[^0-9]/g;
	if(num != ''){
		if(num.match(patt1) == null){
			var first_num = num.substr(0, 1);
			if(first_num == '1'){
				
			}else{
				alert('请输入手机号码！'); /* 首位不为1 */
				$("#phone_number").focus();
				return false;
			}
		}else{
			alert('手机号只能为数字！');
			$("#phone_number").val("");
			$("#phone_number").focus();
			return false;
		}
		if(num.length!=11){
			
			alert('请输入11位手机号！');
			$("#phone_number").val("");
			$("#phone_number").focus();
			return false;
		
		}
	}else{
		alert('请填写手机号！');
		$("#phone_number").focus();
		return false;
	}
	$(".popBoxBg").hide();
	$('.zaPopBox').show();
	setTimeout("$('.zaPopBox').hide()",3000);
	return false;
	
}

function postPhone(){
	var num = $("#phone_number").val();
	if(num.length == 11){			
		$.ajax({
			type: "POST",
			url: "/wx/red_envelope_1111",
			async: true,
			timeout: 15000,
			data: {phone_num:num,hb_id:"003"},
			dataType: "json",
			complete: function(xhr,textStatus)
			{
				if(xhr.status==200){
					var retJson = JSON.parse(xhr.responseText);
					if(retJson['ret'] == 0){
						if(retJson['money']==19.8){
							$("#quan").attr("src","http://img.urfresh.cn/image/product/11-11/quan1.png");
							$("#rule_txt1").html("1、用户关注U掌柜公众号点击“领红包”，或通过红包H5推广页面领取红包，随机抽取最高30元的红包。");
						}
						if(retJson['money']==20){
							$("#quan").attr("src","http://img.urfresh.cn/image/product/11-11/quan2.png");
							$("#rule_txt1").html("1、20元水果券为2张满减抵用券");
						}
						if(retJson['money']==30){
							$("#quan").attr("src","http://img.urfresh.cn/image/product/11-11/quan3.png");
							$("#rule_txt1").html("1、30元水果券为3张满减抵用券	");
						}			
					}else if(retJson['ret'] == -3){
						$("#quan").attr("src","http://img.urfresh.cn/image/product/11-11/guoqi.png");
						$("#rule_txt1").html("1、用户关注U掌柜公众号点击“领红包”，或通过红包H5推广页面领取红包，随机抽取最高30元的红包。");
						//$("#already_have").show();
						//$("#already_txt").html("很抱歉,活动已过期");
						//setTimeout("$('#already_have').hide()",3000);
					}else if(retJson['ret'] == -5){
						$("#quan").attr("src","http://img.urfresh.cn/image/product/11-11/fawan.png");
						$("#rule_txt1").html("1、用户关注U掌柜公众号点击“领红包”，或通过红包H5推广页面领取红包，随机抽取最高30元的红包。");
						//$("#already_have").show();
						//$("#already_txt").html("很抱歉,红包已发完");
						//setTimeout("$('#already_have').hide()",3000);
					}else if(retJson['ret'] == -4){
						$("#quan").attr("src","http://img.urfresh.cn/image/product/11-11/yiling.png");
						$("#rule_txt1").html("1、用户关注U掌柜公众号点击“领红包”，或通过红包H5推广页面领取红包，随机抽取最高30元的红包。");
						//$("#already_have").show();
						//$("#already_txt").html("您已领过奖品");	
						//setTimeout("$('#already_have').hide()",3000);							
					}else if(retJson['ret'] == -2 || retJson['ret'] == -1){
						alert(retJson['msg']);	
					}
				}
				else{
					alert("网络异常，请稍后再试。("+xhr.status+")");
				}
			}
		});
	}
}


(function() {
	var currUrl = window.location.href.replace(window.location.hash, '');
	
	var title1 = '魔都惊现水果霸王餐，我已加入，你还不来？';
	var title2 = 'U掌柜，水果零食1小时送达。双11最高领30元水果券，还能砸出免单霸王餐！';
	var title3 = '这个双11，魔都惊现一种新的霸王餐吃法';
	var img_url = 'http://wx.urfresh.cn/static/hb/images/11-11/hb.jpg';
	var hb_url = currUrl;
	$.ajax({
		type: "POST",
		url: "/wx/signature",
		async: true,
		timeout: 15000,
		data: {currUrl:currUrl},
		dataType: "json",
		complete: function(xhr,textStatus)
		{
			if(xhr.status==200){
				var retJson = JSON.parse(xhr.responseText);

				//alert(xhr.responseText);

			        wx.config({
			        	debug     : false,
			                appId     : retJson['appid'],
			                timestamp : retJson['timestamp'],
			                nonceStr  : retJson['nonceStr'],
			                signature : retJson['sign'],
			                jsApiList : [
			                    // 所有要调用的 API 都要加到这个列表中
			                    'checkJsApi',
			                    'onMenuShareTimeline',
			                    'onMenuShareAppMessage',
			                    'getNetworkType',
			                    'closeWindow',
			                ],
			                success: function (res) {
			                },
			                fail: function(res) {
			                },
			                complete: function(res) {
			                }
			        });

			        wx.ready(function () {
				        // 分享给朋友
				        wx.onMenuShareAppMessage({
				                title: title1,
				                desc: title2,
				                link: hb_url,
				                imgUrl: img_url,
				                trigger: function (res) {
				                },
				                success: function (res) {
				                },
				                cancel: function (res) {
				                },
				                fail:function (res) {
				                }
				        });
				 
				        // 分享到朋友圈
				        wx.onMenuShareTimeline({
				                title: title3,
				                link: hb_url,
				                imgUrl: img_url,
				                trigger: function (res) {
				                },
				                success: function (res) {
				                },
				                cancel: function (res) {
				                },
				                fail:function (res) {
				                }
				        });
				});
			}
		}
	});

	//$("#title_2").html('here');
})();

