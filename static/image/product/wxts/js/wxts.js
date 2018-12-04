
function jsonpcallback(json) {
    console.log(json)
}

(function() {
	var currUrl = window.location.href.replace(window.location.hash, '');
	var title1 = '新疆出好梨，香甜蜜在心';  // 分享朋友标题
	var title2 = '赶快去U掌柜选购【世界梨后】吧';  // 分享朋友副标题
	var title3 = '梨后驾到，快来接驾~【U掌柜】一小时送达'; // 分享朋友圈标题
	var img_url = 'http://img.urfresh.cn/image/product/wxts/images/icon.png';
	var hb_url = currUrl;
	$.ajax({
		type: "POST",
		url: "http://wx.urfresh.cn/wx/signature",
		async: true,
		timeout: 15000,
		data: {currUrl:currUrl,cross:'yes'},
		dataType: "jsonp",
		jsonp: "callback",
		jsonpCallback:"jsonpcallback",
		//complete: function(xhr,textStatus)
		success: function (data)
		{
			var retJson = data;

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
	});

})();

