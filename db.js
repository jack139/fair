/* -------------- Collections list ---------------*/
base_image
{
	"_id" : ObjectId("5559916645f96e05b1694431"),
	"image" : "ogbqtlqktw.jpeg",
	"refer" : 0,
	"file" : "0000986.jpeg",
	"size" : 27114
}

base_shop
{
	"_id" : ObjectId("5559936945f96e05efbbf344"),
	"available" : 1,
	"people" : "1",
	"image" : [
		"rjheuwyohx.jpeg"
	],
	"worker" : 1,
	"address" : "高思路",
	"name" : "高思路店",
	"note" : "测试",
	"shortname" : "高思路店",
	"history" : [
		[
			"2015-05-18 15:23:21",
			"test",
			"create"
		],
		[
			"2015-05-19 07:03:03",
			"test",
			"update"
		]
	],
	"type" : "chain",
	"abstract" : "测试用",
	"refer" : 1
}

base_sku
{
	"_id" : ObjectId("555992fc45f96e05efbbf340"),
	"available" : 1,
	"fresh_time" : 3,
	"abstract" : "烟台苹果，80cm",
	"image" : [
		"mldtnyuwxx.jpeg"
	],
	"name" : "烟台苹果2",
	"original" : "山东烟台",
	"note" : "",
	"history" : [
		[
			"2015-05-18 15:21:32",
			"test",
			"create"
		],
		[
			"2015-05-20 21:58:59",
			"test",
			"update"
		]
	],
	"refer" : 3
}

sku_store
{
	"_id" : ObjectId("555c4ae645f96e047b294c05"),
	"is_onsale" : 0,
	"shipping" : 1,
	"fresh_time" : 2,

	"product_id" : "k00000004",
	"base_sku" : DBRef("base_sku", ObjectId("555a658045f96e05efbbf356")),
	"wxpay_only" : 1,
	"is_gift" : 0,

	"note" : "",
	"free_delivery" : 0,
	"maximun" : 0,
	"is_pack" : 0, // 设置一次，不可以修改
	"available" : 1,

	"unit_num" : 1, // 设置一次，不可以修改
	"unit" : "kg", // 设置一次，不可以修改
	
	"refer" : 3, // 引用数

	//"price" : "5.00", 价格到门店，sku里不纪录实际价格
	"min_price" : "1.00",  // 参考价格，从base移到store里，供门店价格参考
	"ref_price" : "2.00",
	"max_price" : "999.99",
	"special_price" : "5.00", // is_onsale==1时，有意义
	"ref_cost" : "2.00",

	"history" : [
		[
			"2015-05-20 16:50:46",
			"test",
			"create"
		],
		[
			"2015-05-20 17:15:50",
			"test",
			"update"
		],
	],

	// for 线上app
	"list_in_app" : 1, // 是否app线上销售
	"sort_weight" : 999, // app列表排序，按顺序排，0在最前
	"app_title" : "个个大红富士／4个", // app显示的商品标题
	"promote" : 1, // 是否显示“推荐”标签
	"category" : "001", // 商品类目
}
 
inventory
{
	"_id" : ObjectId("555ed1ac45f96e058f6be88e"),
	"sku" : ObjectId("555c915145f96e059408a38e"),
	"shop" : ObjectId("5559936945f96e05efbbf344"),
	"product_id" : "w000001",  // w－称重 k－包装 u-未称重
	"weight" : "1.00", // w-only, 其他为 0
	"price" : "5.00", // 各门店单价
	"total" : "5.00", // w-only 称重后总价
	"online" : 1, // 上下架
	"num" : 3, //  库存数量， w-item为 1，售出后为 0
	"history" : [
		[
			"2015-05-22 14:50:20",
			"test",
			"create 1"
		],
		[
			"2015-05-22 14:50:34",
			"test",
			"update 1 to 3"
		]
	],

	// 冗余，便于app检索商品
	"list_in_app" : 1, // 是否app线上销售
	"sort_weight" : 999, // app列表排序，按顺序排，0在最前
	"category" : "001",
}

order_stock // 仓储工单单
{
	"type" : "", // SEND 发货单， BOOK 订货单， WORK 加工单
	"status" : "on-road", // 发货单状态： wait 等待备货，ready 准备发货，on-road 在途，on-shop 到店，confirm 确认收货，return 退货，finish 结束
			   // 订货单状态： wait 等待处理，sent 已出发货单，refuse 拒绝，finish 结束
	"history" : [
		[
			"2015-05-22 14:50:20",
			"test",
			"create"
		],
	]

	// 发货单属性
	"shop_to" : ObjectId("5559936945f96e05efbbf344"),
	"shop_from" : ObjectId("5559936945f96e05efbbf344"),
	"cart" : [{
		"product_id" : "",
		"num" : 0,
		"name" : "",
		"cost_price" : 0, //  cost_price在发货的时候才有意义
		"onload" : 0, // 发货时才有意义
	}], 
}

order_offline // 销货单
{
	"status" : 'DUE', // 订单状态： due 待付， paid 已付， cancel 取消， finish 结束
	"shop" : ObjectId("5559936945f96e05efbbf344"),
	"order_id" : "f0000001",  // f - 线下订单，e - 线上订单
	"item" : [{"product_id":"", "num":"", "price":"", "name":"", "cost":""}], // sku
	"cost" : "0.00", // 成本合计
	"total": "0.00", // 价格总计
	"discount": "0.00", // 折扣
	"due" : "0.00", // 应付价格
	"pay" : "0.00", // 实付
	"change" : "0.00", // 找零
	"date" : "2015-06-03",
	"history" : [
		[
			"2015-05-22 14:50:20",
			"test",
			"create"
		],
	]
}


shop_audit // 门店盘点
{
	"shop" : ObjectId("5559936945f96e05efbbf344"),
	"status" : "OPEN", // 盘点状态 OPEN－账期开放，CLOSED-账期结束（已盘点）
	"begin_date" : "2015-06-01", // 期初日期
	"end_date" : "2015-06-01", // 期末日期
	// 以下价格都用 ref_price
	"stock" : [], // 盘点数据, 
	//{
	//	'k00001' : { 
	//		'begin'   : (<ref_price>, <num>), 上一账期的均价，期初为0，则以参考价
	//		'end'     : (<ref_price>, <num>), 期初＋进货 的均价
	//		'audit'   : (<ref_price>, <num>), 期初＋进货 的均价
	//		'loss'    : (<ref_price>, <num>), 损耗数量、金额
	//		'sale'    : (<ref_price>, <num>), 销售数量、成本金额
	//	}
	//}
	"gross" : "10.00", // 总毛利
	"loss" : "10.00", // 总耗损
	"cost" : "10.00",  // 总销售成本
	"revenue" : "10.00", // 总销售收入

	// 数量：盘点＋损耗 ＝ 期末 ＝ 期初 ＋ 进货 － 销售
	//      盘点 － 期末 ＝ 损耗

	// 毛利额：销售额-(期初+进货-盘点)*ref_price

	// ref_price应该维持一个平均价，同一个sku每次进货进行调整？
}

app_user // app用户
{
	"_id" : ObjectId("55aa79e245f96e0ae4a6527c"),
	"reg_time" : "2015-07-19 00:08:02", // 注册时间
	"coupon" : [ // 优惠券
		[
			"fitf",  // id
			"2015-08-18",  // 有效期
			"5.00",  // 抵扣金额
			1 // 1-未用， 0-已用
		]
	],
	"app_id" : "W853BV9B", // 注册时的app_id
	"uname" : "13194084665", // 手机号码
	"address" : [   // 收货地址
		[
			"fitf",  // id
			"张三",  // 收货人
			"13800000000",  // 电话
			"高斯路1122弄" // 地址
		]
	],
	"last_time" : "2015-07-19 00:14:11"  // 最近登录时间
}

order_app   // 线上订单
{
	"_id" : ObjectId("55eb871531c98b1e4f8fd617"),
	"order_id" : "n016602",
	"shop" : ObjectId("55d968fb5e0bdc65b295e9f2"),
	"comment" : "",
	"coupon" : [
		"xduy",
		"2015-10-05",
		"6.00",
		1
	],
	"lock" : 0,
	"delivery_fee" : "0.00",
	"uname" : "13695588156",
	"cost" : "29.96",
	"deadline" : 1441499881,
	"total" : "37.30",
	"retry" : 0,
	"first_disc" : "0.00",
	"due" : "31.30",
	"status" : "ONROAD",
	"e_time" : 1441498981,
	"cart" : [
		{
			"cost" : "5.06",
			"product_id" : "k000235",
			"num2" : 1,
			"title" : "浙江杭州湾巨峰葡萄（500g）",
			"price" : "4.90",
			"num" : 1
		},
		{
			"cost" : "3.47",
			"product_id" : "k000261",
			"num2" : 1,
			"title" : "上海蜜梨 2只装（约500g）",
			"price" : "4.90",
			"num" : 1
		},
		{
			"cost" : "9.50",
			"product_id" : "k000258",
			"num2" : 1,
			"title" : "新西兰佳沛绿果猕猴桃 3粒装（300g）",
			"price" : "8.80",
			"num" : 1
		},
		{
			"cost" : "3.15",
			"product_id" : "k000248",
			"num2" : 1,
			"title" : "越南龙眼 1盒装（220g）",
			"price" : "4.90",
			"num" : 1
		},
		{
			"cost" : "5.19",
			"product_id" : "k000236",
			"num2" : 1,
			"title" : "云南红提 1盒装（约500g）",
			"price" : "8.90",
			"num" : 1
		},
		{
			"cost" : "3.59",
			"product_id" : "k000260",
			"num2" : 1,
			"title" : "山东爽口水果黄瓜 3根装（300g）",
			"price" : "4.90",
			"num" : 1
		}
	],
	"user" : "13695588156",
	"address" : [
		"datr",
		"子君",
		"13695588156",
		"西藏北路605设计部",
		1441261004
	],
	"coupon_disc" : "6.00",
	"man" : 0,
	"b_time" : 1441498981,
	"next_status" : "",
	"history" : [
		[
			"2015-09-06 08:23:01",
			"13695588156",
			"提交结算"
		],
		[
			"2015-09-06 08:23:22",
			"alipay",
			"付款通知"
		],
		[
			"2015-09-06 08:23:25",
			"13695588156",
			"提交付款"
		],
		[
			"2015-09-06 10:08:21",
			"hct001",
			"拣货完成"
		],
		[
			"2015-09-06 10:17:13",
			"hct001",
			"开始派送"
		]
	],
	"paid_tick" : 1441499002,
	"ali_trade_no" : "2015090600001000100077872243",
	"paid_time" : "2015-09-06 08:23:22",
	"ali_notify" : [
		{
			"seller_email" : "pay@urfresh.cn",
			"sign" : "b+GE3KKB0xzuOeZGsgzmTU0gKyCOgBtQvMjMvI0NI6JE9TdPq2PCyOzeRZig7UP/Lcv9PpSNulkn2h2FVbNPrYLKddk1N10WVAmgHojKkoDaZiPVCe93ESHhuSJSOaqnLVZaROoCcoKxJfvsdAuHuyucEtsov5QTrpYFHPe0REg=",
			"subject" : "U 掌柜",
			"is_total_fee_adjust" : "N",
			"gmt_create" : "2015-09-06 08:23:21",
			"out_trade_no" : "n016602",
			"sign_type" : "RSA",
			"body" : "n016602",
			"price" : "31.30",
			"buyer_email" : "13695588156",
			"discount" : "0.00",
			"trade_status" : "TRADE_SUCCESS",
			"gmt_payment" : "2015-09-06 08:23:22",
			"trade_no" : "2015090600001000100077872243",
			"seller_id" : "2088021137384128",
			"use_coupon" : "N",
			"payment_type" : "1",
			"total_fee" : "31.30",
			"notify_time" : "2015-09-06 08:23:22",
			"quantity" : "1",
			"notify_id" : "0d088f7d4ce8922f4541c8b577a93abc2k",
			"notify_type" : "trade_status_sync",
			"buyer_id" : "2088702759217109"
		}
	],
	"pay_type" : "ALIPAY",
	"paid2_time" : "2015-09-06 08:23:25",
	"paid2_tick" : 1441499005,
	"pay" : "31.30",
	"runner" : {
		"uname" : "hct001",
		"tel" : "未知",
		"name" : "火车头店"
	}
}



/* 拼团 */

pt_store
{
	'tuan_id' : 't000002', // 拼团活动id
	'product_id' : ['1130000277'], // 商品信息
	'title' : '黑心黄心蜜柚各一个，共19.9元', // 标题
	'desc' : '黑黄组合来了！一次解决既吃黑又吃黄，一次吃爽，每个重约2.5公斤。', // 文描
	'price' : '38.90', // 单人价
	'tuan_price' : '28.90', // 拼团价,
	'ref_price' : '45.00', // 市场参考价,
	'volume' : 130, // 成团销量
	'promote' : 0, // 是否促销（标签）
	'image' : ['/test/ptSkuPic2.jpg'], // 活动图片
	'tuan_size' : 4, // 成团人数
	'region_id' : ['001'], // 区域标记, 可能再多个区域存在
	'expire_tick' : 1446998785, // 到期tick
	'expire_time' : '2015-12-01 23:23:23', // 到期时间
	'online' : 1, // 上下架
	'sale_out' : 0, // 是否售罄 1 售罄， 0 未售罄
	'sort_weight' : 999, // 显示排序权重
	'history' : [
		"2015-11-06 10:17:13",
		"test2",
		"创建活动"
	]
}

pt_order
{
	'tuan_id' : 't00001', // 拼团活动
	'pt_order_id' : 't00001', // 拼团活动
	'region_id' : '001', // 区域标记
	'expire_tick' : 141928345, // 到期tick
	'expire_time' : '2015-11-09 23:23:23', // 到期时间
	'create_tick' : 141928345, // 创建tick
	'create_time' : '2015-11-09 23:23:23', // 创建时间
	'leader' : 'dksalfdsad', // 团长的openid
	'member' : [  // 成员列表
		{
			'openid': 'sdaas',
			'position' : 'LEADER', // LEADER 团长，SECOND 沙发, MEMBER 团员
			'time' : '2015-11-09 23:23:23', // 参团时间
			'image' : 'http://...', // 头像url
		},
		{
			'openid': 'dsfdaf',
			'position' : 'SECOND', 
			'time' : '2015-11-09 23:23:23', // 参团时间
			'image' : 'http://...', 
		}
		{
			'openid': 'dsfdaf',
			'position' : 'MEMBER', 
			'time' : '2015-11-09 23:23:23', // 参团时间
			'image' : 'http://...', 
		}
	], 
	'need' : 2, // 还需几人成团
	'type' : 'TUAN', // TUAN 拼团 SINGLE 个人购买
	'status' : 'OPEN', // 状态 OPEN 拼团中 SUCC 已成团 FAIL1 超时失败 FAIL2 售罄失败
}

/* -------------- Indexes ---------------*/

db.user.createIndex({privilege:1})
db.user.createIndex({uname:1})
db.user.createIndex({login:1, privilege:1})

db.sessions.createIndex({session_id:1})

db.app_device.createIndex({app_id:1})

db.app_sessions.createIndex({session_id:1})

db.app_user.createIndex({uname:1})
db.app_user.createIndex({uname:1, mice:1})
db.app_user.createIndex({app_id:1})
db.app_user.createIndex({openid:1})
db.app_user.createIndex({openid:1, mice:1})
db.app_user.createIndex({my_invit_code:1})

db.order_app.createIndex({order_id:1})
db.order_app.createIndex({user:1, status:1})
db.order_app.createIndex({user:1, status:1, order_id:1})
db.order_app.createIndex({order_id:1, user:1})
db.order_app.createIndex({uname:1, order_id:1})
db.order_app.createIndex({uname:1, status:1, deadline:1})
db.order_app.createIndex({status:1, deadline:1})
db.order_app.createIndex({order_id:1, shop:1})

db.order_app.createIndex({shop:1, status:1})
db.order_app.createIndex({shop:1, status:1, type:1})
db.order_app.createIndex({shop:1, status:1, type:1, 'address.8':1})

db.order_app.createIndex({pt_order_id:1, status:1})
db.order_app.createIndex({pt_order_id:1, uname:1})

db.base_shop.createIndex({available:1})
db.base_shop.createIndex({name:1})

db.base_sku.createIndex({name:1})
db.base_sku.createIndex({original:1})
db.base_sku.createIndex({available:1})

db.base_image.createIndex({image:1})

db.sku_store.createIndex({product_id:1})
db.sku_store.createIndex({base_sku:1})
db.sku_store.createIndex({product_id:1, base_sku:1})

db.inventory.createIndex({sku:1})
db.inventory.createIndex({shop:1})
db.inventory.createIndex({product_id:1, shop:1})
db.inventory.createIndex({sku:1, shop:1})

db.shop_audit.createIndex({shop:1})
db.shop_audit.createIndex({shop:1, status:1})
db.shop_audit.createIndex({_id:1, shop:1,})

db.order_stock.createIndex({shop:1})
db.order_stock.createIndex({type:1})
db.order_stock.createIndex({type:1, status:1, product_id:1, shop_from:1, shop_to:1})

db.order_offline.createIndex({shop:1})
db.order_offline.createIndex({order_id:1, shop:1})

db.recv_tel.createIndex({tel:1})

db.recv_addr.createIndex({addr:1})

db.addr_fail.createIndex({addr:1})

db.hb_store.createIndex({phone:1})
db.hb_store.createIndex({hb_id:1})

db.credit_card.createIndex({card_no:1})
db.credit_card.createIndex({card_no:1,used:1})

db.sms_sent_log.createIndex({mobile:1})

db.pt_store.createIndex({tuan_id:1})
db.pt_store.createIndex({tuan_id:1,region_id:1})
#db.pt_store.createIndex({region_id:1,online:1,expire_tick:1})

db.pt_order.createIndex({pt_order_id:1,'member.openid':1})
db.pt_order.createIndex({region_id:1,'member.openid':1,leader:1})
db.pt_order.createIndex({pt_order_id:1,need:1,status:1})
db.pt_order.createIndex({pt_order_id:1})
db.pt_order.createIndex({tuan_id:1})
db.pt_order.createIndex({status:1,expire_tick:1})



/* ------------- db ------------------ */

