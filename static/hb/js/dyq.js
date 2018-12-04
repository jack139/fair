

(function() {
	var currUrl = window.location.href.replace(window.location.hash, '');
	var title1 = '@U掌柜一起，品醉美黑珍珠葡萄，看杨幂&鹿晗飙演技！';
	var title2 = '10月28日U掌柜下单，享14.9元黑珍珠葡萄买1送1，19.9元包邮，送10元电影优惠券看大片！';
	var title3 = '@U掌柜一起，品醉美黑珍珠葡萄，看杨幂&鹿晗飙演技！';
	var img_url = 'http://wx.urfresh.cn/static/hb/images/sg/sg.jpg';
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

