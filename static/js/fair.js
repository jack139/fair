$(document).ready(function () {
    document.addEventListener('WeixinJSBridgeReady', function onBridgeReady() {
        WeixinJSBridge.call('hideOptionMenu');
    });

    $('#cart').on('click' , function (){
        $('#menu-container').hide();
        $('#cart-container').show();
        $('#user-container').hide();

        $(".footermenu ul li a").each(function(){
            $(this).attr("class","");
        });
        $(this).children("a").attr("class","active");

        //Ax201500308: 两步结算，显示购物车
        goCartPage();
    });

    $('#home').on('click' , function (){
        $('#menu-container').show();
        $('#cart-container').hide();
        $('#user-container').hide();

        $(".footermenu ul li a").each(function(){
            $(this).attr("class","");
        });
        $(this).children("a").attr("class","active");

        $('#product').hide();
        $('#banner').show();

        if($('#loadsalesproduct').length > 0){
            return;
        }
        else{
            //Get limited products
            var limitedProductArr = getLimitedProduct();

            $.ajax({
                type : 'POST',
                //url : apiurl+'api.php?method=getOnSaleProduct&uid='+uid+'&customer_id='+customer_id+'&station_id='+station_id+'&language_id='+language_id,
                url : apiurl+'sku_onsale',
                data : {
                    //method : 'getOnSaleProduct',
                    uid : uid,
                    id : 0
                },
                success : function(response , status , xhr){
                    //$('#product').show();
                    //var json = response;
                    var json = eval(response);

                    var productHtml = '';

                    var productHtml_0 = '';

                    $.each(json, function(index, value){
                        var onsale_tag = '';
                        var onsle_tag_price = '';
                        var product_abstract = '';

                        var productHtml_pre = productHtml;


                        //Filter limited product
                        if($.inArray(value.product_id,limitedProductArr) >=0 ){
                            return true; //Jump and continue next loop;
                        }

                        if(value.price > value.special_price){
                            onsale_tag = '<span class="onsale"><i>特价》</i></span>';
                            onsle_tag_price = '<del>'+value.price+'</del>';
                        }

                        if(value.abstract !== ''){
                            product_abstract = ' <span class="product_abstract"><i>'+value.abstract+'</i></span>';
                        }

                        productHtml += '<dd id="loadsalesproduct">';
                        productHtml +=      '<div class="tupian">';
                        productHtml +=      '<img class="saleproductimage" data-original="'+imgpath+value.image+'" src="/static/image/lazyload.jpg" style="height:4em; width:4em">';
                        productHtml +=          '<p class="dish2">'+onsale_tag+value.name+'</p>';
                        productHtml +=          '<p class="price2">'+value.special_price+'元/'+value.unit_amount+value.unit_title+'</p>';
                        productHtml +=          '<p>'+onsle_tag_price+product_abstract+'</p>';
                        productHtml +=      '</div>';
                        productHtml +=      '<div class="listproductadd" id="saleproductadd_'+value.product_id+'" style="display: block; right:0px;">';
                        productHtml +=          '<a href="javascript:doProduct(\''+ value.product_id+'\',\''+value.name+'\',\''+value.special_price+'\',\''+value.price+'\');" id="'+value.product_id+'" class="reduce"><b class="ico_reduce_start">-</b></a>';
                        productHtml +=      '</div>';

                        productHtml +=      '<div id="saleproductchange_'+value.product_id+'" class="orderchange" style="display: none; right:-200px">';
                        productHtml +=          '<a href="javascript:addProductN(\''+ value.product_id+'\',\''+value.special_price+'\');" class="increase"><b class="ico_increase">+</b></a>';
                        productHtml +=          '<span name="cartitem_count" class="count" id="saleproductnum_'+value.product_id+'">0</span>';
                        productHtml +=          '<a href="javascript:reduceProductN(\''+ value.product_id+'\',\''+value.special_price+'\');" class="reduce"><b class="ico_reduce">-</b></a>';
                        productHtml +=      '</div>';
                        productHtml += '</dd>';

//                        if(value.special_price == 0){
//                            productHtml_0 += productHtml;
//                            $('#specialproductinsert').append( productHtml_0 );
//                            productHtml = ''; //TODO sort problem
//                            $('#promotion_hold').show();
//                        }
//                        else{
//                            $('#promotion_hold').hide();
//                        }

                        //if(value.product_id == 1489){

                        if(value.special_price == 0){
                            productHtml_0 += productHtml;
                            $('#promotionproductinsert').append(productHtml_0);
                            productHtml = productHtml_pre; //Ignore this loop, filter 0 product
                            $('#promotionhold').show();
                        }


                    });

                    //$('#productlistinsert').empty();
                    $('#specialproductinsert').append( productHtml );

                    if(productHtml_0 == ''){
                        $('#promotion_hold').hide();
                    }

                    //Alex: 2015-04-12, Use lazy load to load product images
                    $(".saleproductimage").lazyload({effect:"fadeIn", threshold:200});
                },
                beforeSend : function(){
                    $('#product-load').show();
                },
                complete : function(){
                    $('#product-load').hide();
                }
            });
        }
    });

    $('#user').on('click' , function (){
        $('#menu-container').hide();
        $('#cart-container').hide();
        $('#user-container').show();

        $(".footermenu ul li a").each(function(){
            $(this).attr("class","");
        });
        $(this).children("a").attr("class","active");

        //Get Credits
        $.ajax({
            type : 'POST',
            //url : apiurl+'api.php',
            url : apiurl+'customer_credit',
            data : {
                //method : 'getCustomerCredit',
                uid : uid,
                id : customer_id
            },
            success : function (response , status , xhr){
                if(response){
                    var credit = eval(response);
                    $('#current_credit').html(credit);
                }
            }
        });

        //Get Orders
        $.ajax({
            type : 'POST',
            //url : apiurl+'api.php',
            url : apiurl+'order_by_customer',
            data : {
                //method : 'getOrderByCustomer',
                uid : uid,
                id : customer_id
            },
            success : function (response , status , xhr){
                if(response){
                    var json = eval(response);
                    var html = '';
                    var payment_status = '';
                    var due = '';
                    var order_deliver_status = '';
                    var payment_style = '';

                    $.each(json, function (index, value) {
                        payment_status = '<br />';
                        if(value.payment_code=='WXPAY' && value.order_payment_status_id == 1){
                            payment_status += '<a class="wxpay" href="javascript:processPayment('+value.order_id+');" >现在支付</a>';
                        }
                        else{
                            payment_status += value.order_payment_status;
                        }

                        due = '<br />(' + value.due + '元)';
                        order_deliver_status = '<br />' + value.order_deliver_status;
                        if(value.order_status_id == 3){ //订单已取消
                            payment_status = '';
                            due = '';
                            order_deliver_status = '';
                        }

                        if(value.order_payment_status_id == 2){
                            payment_style = 'class="colorgreen"';
                        }


                        html += '<tr>' +
                        //html += '<tr>' +
                            '<td onclick="javascript:showOrderDetail(\''+value.order_id+'\');" >'+value.order_id.substr(-5)+'<br />'+value.order_status+'</td>' +
                            '<td onclick="javascript:showOrderDetail(\''+value.order_id+'\');" class="cc">'+value.order_total+due+'</td>' +
                            '<td class="cc" '+payment_style+'><b>'+value.payment_method+payment_status+'</b></td>' +
                            '<td onclick="javascript:showOrderDetail(\''+value.order_id+'\');" class="cc"><b>'+value.deliver_date+order_deliver_status+'</b></td>' +
                            '</tr>';
                    });
                    $('#orderlistinsert').empty();
                    $('#orderlistinsert').append( html );
                }
            },
            beforeSend : function(){
                $('#page_tag_load').show();
            },
            complete : function(){
                $('#page_tag_load').hide();
            }
        });
    });

});

/*PROCESS PAYMENT START*/
function processPayment(order_id){
    //Get Credits
    $.ajax({
        type : 'POST',
        //url : apiurl+'api.php?method=getOrderTotal',
        url : apiurl+'order_total',
        data : {
            //method : 'getOrderTotal',
            uid : uid,
            id : order_id
        },
        success : function (response , status , xhr){

            if(response){
                //var json = eval(response); //For JSON Array
                //var due = 0;
                //$.each(json, function (index, value) {
                //    due = value.due;
                //});
                var json = $.parseJSON(response); //For JSON String
                //Now we have dueTotal, due, order_id, payment_code, order_status_id, order_payment_status_id

                //Process WX PAY
                if(json.order_status_id == 3){ //订单取消
                    alert('订单['+order_id+']已取消，无法支付。');
                    return false;
                }
                else if(json.dueTotal = 0 && json.payment_code == 'FREE' ){ //零元订单－促销活动，限自提，无需支付。
                    myOrder();
                }
                else if(json.dueTotal < 0 && json.payment_code !== 'CREDIT' ){ //订单无应付金额，除余额支付
                    alert('订单['+order_id+']支付金额有误，请联系我们。');
                    return false;
                }
                else if(json.payment_code =='WXPAY'){
                    location="payment/wxpay.php?showwxpaytitle=1&order_id="+order_id+"&uid="+uid+"&total="+json.due;
                }
                else{
                    //myOrder();
                    return false;
                }
            }

        }
    });


}
/*PROCESS PAYMENT END*/

function myOrder(){
    $('#user').click();
}

function home(){
    $('#home').click();
    $('#menu ul li a').removeClass('menu_selected');
    $('#menu_0 a').addClass('menu_selected');

    showAll();
}
function clearCache(){
    $('#ullist').find('li').remove();

    $('#home').click();

    $('.reduce').each(function () {
        $(this).children().css('background','');
    });
    $('#totalNum').html(0);
    $('#cartN2').html(0);
    $('#totalPrice').html(0);

    $('#shipping_fee').val(0);
    $('#order_total').val(0);
    $('#cart_total').val(0);
    $('#discount_fee').val(0);
}
function addProductN(id,price){

    //处理商品列表部分
    var thisproductnumid = '#listproductnum_'+id;
    var saleproductnumid = '#saleproductnum_'+id; //On Sale

    //获取已添加的值
    var saleproductnum = parseInt($(saleproductnumid).html());
    var thisproductnum = saleproductnum;
    if($(thisproductnumid).length){
        thisproductnum = parseInt($(thisproductnumid).html());
    }

    //TODO 商品数量限制，首次有效订单
    if(thisproductnum > 19){
        alert('单件商品数量不能超过20');
        return false;
    }
    if(saleproductnum > 2){
        alert('特价商品数量不能超过3');
        return false;
    }

    if(id==1489 && saleproductnum > 0){
        alert('零元购鸡蛋仅限1份');
        return false;
    }

    thisproductnum += 1;

    $(thisproductnumid).html(thisproductnum);
    $(saleproductnumid).html(thisproductnum);

    //处理购物车列表部分
    var cartnumid = "#cartnum_"+id;
    var productN = parseFloat( $(cartnumid).html());

    $(cartnumid).html( productN + 1);

    var cartMenuN = parseFloat($('#cartN2').html())+1;

    $('#totalNum').html( cartMenuN );
    $('#cartN2').html( cartMenuN );

    var totalPrice = parseFloat($('#totalPrice').html())+ parseFloat(price);
    $('#totalPrice').html( totalPrice.toFixed(2) );
}

function reduceProductN(id,price){

    //处理商品列表部分
    var thisproductnumid = '#listproductnum_'+id;
    var saleproductnumid = '#saleproductnum_'+id;

    //获取已添加的值
    var thisproductnum = parseInt($(saleproductnumid).html());
    if($(thisproductnumid).length){
        thisproductnum = parseInt($(thisproductnumid).html());
    }

    //不可少于0
    if(thisproductnum == 1){
        showProductAdd(id);
    }

    if(thisproductnum > 0){
        thisproductnum -= 1;
    }

    $(thisproductnumid).html(thisproductnum);

    //On Sale
    $(saleproductnumid).html(thisproductnum);

    //处理购物车列表部分
    var cartnumid = "#cartnum_"+id;
    var cartid = "#wemall_"+id;

    var reduceProductN = parseFloat( $(cartnumid).html());
    if ( reduceProductN == 1) {
        $(cartid).remove();
        var id = cartid.split('_')[1];
        $('#'+id).children().css('background','');

        if ( $('#ullist').find('li').length == 0 ){
            $('#menu-container').show();
            $('#cart-container').hide();
            $('#user-container').hide();
        }
    }

    $(cartnumid).html( reduceProductN - 1);

    var cartMenuN = parseFloat($('#cartN2').html())-1;
    $('#totalNum').html( cartMenuN );
    $('#cartN2').html( cartMenuN );

    var totalPrice = parseFloat($('#totalPrice').html())- parseFloat(price);
    $('#totalPrice').html( totalPrice.toFixed(2) );
}

function doProduct (id , name , price, oldprice) {

    var thisproductnumid = '#listproductnum_'+id;
    var saleproductnumid = '#saleproductnum_'+id; //On Sale

    var thisproductnum = 0; //商品动态载入，不可取值
    if($(saleproductnumid).length){
        thisproductnum = parseInt($(saleproductnumid).html());
    }
    if($(thisproductnumid).length){
        thisproductnum = parseInt($(thisproductnumid).html());
    }

    if(thisproductnum > 0){
        return false; //商品已添加，不再执行doProduct
    }
    thisproductnum += 1;
    $(thisproductnumid).html(thisproductnum);

    //On Sale
    $(saleproductnumid).html(thisproductnum);

    showProductChange(id);

    //console.log($(thisproductnumid).html());

    var cartMenuN = parseFloat($('#cartN2').html())+1;
    $('#totalNum').html( cartMenuN );
    $('#cartN2').html( cartMenuN );

    var totalPrice = parseFloat($('#totalPrice').html())+ parseFloat(price);
    $('#totalPrice').html( totalPrice.toFixed(2) );

    var wemallId = 'wemall_'+id;
    var html = '<li class="ccbg2" id="'+wemallId+'"><div class="orderdish"><span name="cartitem_id" class="hide">'+id+'</span><span name="cartitem_oldprice" class="hide">'+oldprice+'</span><span name="cartitem_title">'+name+'</span><span name="cartitem_price" class="price">'+price+'</span><span class="price">元</span></div><div class="orderchange"><a href=javascript:addProductN('+id+','+price+') class="increase"><b class="ico_increase">加一份</b></a><span name="cartitem_count" class="count" id="cartnum_'+id+'">1</span><a href=javascript:reduceProductN('+id+','+price+') class="reduce"><b class="ico_reduce">减一份</b></a></div></li>';
    $('#ullist').append(html);

}

function showProductAdd(id){
    var thisproductchangeid = '#listproductchange_'+id;
    var listproductaddid = '#listproductadd_'+id;

    //On Sale
    var saleproductchangeid = '#saleproductchange_'+id;
    var saleproductaddid = '#saleproductadd_'+id;

    $(listproductaddid).show();
    $(thisproductchangeid).hide();
    $(thisproductchangeid).animate({right:'-200px'});

    //On Sale
    $(saleproductaddid).show();
    $(saleproductchangeid).hide();
    $(saleproductchangeid).animate({right:'-200px'});
}

function showProductChange(id){
    var thisproductchangeid = '#listproductchange_'+id;
    var listproductaddid = '#listproductadd_'+id;

    //On Sale
    var saleproductchangeid = '#saleproductchange_'+id;
    var saleproductaddid = '#saleproductadd_'+id;

    $(listproductaddid).hide();
    $(thisproductchangeid).show();
    $(thisproductchangeid).animate({right:'0px'});

    //On Sale
    $(saleproductaddid).hide();
    $(saleproductchangeid).show();
    $(saleproductchangeid).animate({right:'0px'});

}
function resetProductlist(id){
    var thisproductnumid = '#listproductnum_'+id;
    $(thisproductnumid).html(0);

    //On Sale
    var saleproductnumid = '#saleproductnum_'+id;
    $(saleproductnumid).html(0);

    showProductAdd(id);
}

function submitOrder () {
    //获取订单信息
    //TODO 重新获取购物车信息，使用缓存

    var json = '';
    var submittedItem = new Array();
    $('#ullist li').each(function () {
        var name = $(this).find('span[name=cartitem_title]').html();
        var num = $(this).find('span[name=cartitem_count]').html();
        var price = $(this).find('span[name=cartitem_price]').html();
        var oldprice = $(this).find('span[name=cartitem_oldprice]').html();
        var itemid = $(this).find('span[name=cartitem_id]').html();
        json += '{"itemid":"'+itemid+'","name":"'+name+'","num":"'+num+'","price":"'+price+'","oldprice":"'+oldprice+'"},';

        submittedItem.push(itemid);
    });
    json = json.substring(0 , json.length-1);
    json = '['+json+']';

    $.ajax({
        type : 'POST',
        //url : apiurl+'api.php?method=addOrder&uid='+uid+'&customer_id='+customer_id+'&station_id='+station_id+'&language_id='+language_id,
        url : apiurl+'order_add',
        data : {
            //method : 'addOrder', //addOrder
            uid : uid,
            station_id : station_id,
            language_id : language_id,
            cartData : json,
            //userData : $('#infoForm').serializeArray()
            userData : $('#infoForm').serialize()
        },
        success : function (response , status , xhr) {

            if(response == 'false'){
                alert("订单数据错误，请检查购物车商品，例如0元购商品只能购买一次，如问题依旧请通过微信联系我们。");
                return false;
            }


            //Order success, now show order list
            //$('#user').click();
            $('#ullist').find('li').remove();
            $('.reduce').each(function () {
                $(this).children().css('background','');
            });
            $('#totalNum').html(0);
            $('#cartN2').html( 0 );
            $('#totalPrice').html(0);

            //Reset homepage & product list
            $('#promotionproductinsert').html('');
            $('#promotionhold').hide();

            $('#specialproductinsert').html('');
            $('#productlistinsert').html('');


            for(var m=0,n=submittedItem.length; m<n; m++){ //提交订单后重置列表商品选择部分
                resetProductlist(submittedItem[m]);
            }

            if( $('#pay').val()==1 ){ //如果是微信支付直接支付
                //TODO update credit
                processPayment(response);
            }
            else{
                myOrder();
            }

        },
        beforeSend : function(){
            $('#menu-shadow').show();
        },
        complete : function(){
            $('#menu-shadow').hide();
        }
    });


}

var $_GET = (function(){
    var url = window.document.location.href.toString();
    var u = url.split("?");
    if(typeof(u[1]) == "string"){
        u = u[1].split("&");
        var get = {};
        for(var i in u){
            var j = u[i].split("=");
            get[j[0]] = j[1];
        }
        return get;
    } else {
        return {};
    }
})();

String.prototype.colorHex = function(){
    var that = this;
    if(/^(rgb|RGB)/.test(that)){
        var aColor = that.replace(/(?:\(|\)|rgb|RGB)*/g,"").split(",");
        var strHex = "#";
        for(var i=0; i<aColor.length; i++){
            var hex = Number(aColor[i]).toString(16);
            if(hex === "0"){
                hex += hex;
            }
            strHex += hex;
        }
        if(strHex.length !== 7){
            strHex = that;
        }
        return strHex;
    }else if(reg.test(that)){
        var aNum = that.replace(/#/,"").split("");
        if(aNum.length === 6){
            return that;
        }else if(aNum.length === 3){
            var numHex = "#";
            for(var i=0; i<aNum.length; i+=1){
                numHex += (aNum[i]+aNum[i]);
            }
            return numHex;
        }
    }else{
        return that;
    }
};

function showDetail(id){
    $.ajax({
        type : 'post',
        url : appurl+'/App/Index/fetchgooddetail',
        data : {
            id : id,
        },
        success : function(response , status , xhr){
            $('#mcover').show();
            var json = eval(response);
            $('#detailpic').attr('src',rooturl+'/Public/Uploads/'+json.image);
            $('#detailtitle').html(json.title);
            $('#detailinfo').html(json.detail);
        }
    });
}
function showMenu(){
    $("#menu").find("ul").toggle();
}
function toggleBar(){
    $(".footermenu ul li a").each(function(){
        $(this).attr("class","");
    });
    $(this).children("a").attr("class","active");
}
function showProducts(id) {
    //getProducts(id);

    $('.menu .ccbg dd').each(function(){
        if( $(this).attr("menu") == id ){
            $(this).show();
        }else{
            $(this).hide();
        }
    });

    //$('#menu ul').hide();
    $('#banner').hide();
    $('#product').show();

    //Setup breadcrumbs, the parent part set by sliding menu
    var thisMenu = '#menu_'+id;
    var thisMenuText = $(thisMenu).text();
    $(".breadcrumbsChild").html(thisMenuText);

    $('#menu ul li a').removeClass('submenu_selected');
    $(thisMenu).children("a").addClass('submenu_selected');

}

function showParentProducts(id){
    getProducts(id);

    $('.menu .ccbg dd').each(function(){
        if( $(this).attr("parent") == id ){
            $(this).show();
        }else{
            $(this).hide();
        }
    });

    //$('#menu ul').hide();
    $('#banner').hide();
    $('#product').show();
}

function showAll() {
    $('.menu .ccbg dd').each(function(){
        $(this).show();
    });
    //$('#menu ul').hide();
}

function nouse_animateMenu(id){
    $("#menuall ul li").animate({opacity:'1.0',paddingLeft:'3px'},30);

    var thismenu = '#menu_'+id;
    var thismenupath = $("#menu_0").html()+' > ';

    if(id > 0){
        $(thismenu).animate({opacity:'0.7',paddingLeft:'10px'},200);
        thismenupath = $("#menu_0").html()+' > '+$(thismenu).html();
    }
    $("#breadcrumbs").html(thismenupath);
}


function showLocPanel(){
    $("#location_panel").show();
    $("#location_panel_bg").show();
    $("#location_panel").animate({top:'0px'});
    $("#location_panel_bg").animate({opacity:'0.5'});
}

function hideLocPanel(){
    $("#location_panel_bg").animate({opacity:'0'});
    $("#location_panel").animate({top:'-100px'});
    $("#location_panel_bg").hide();
    $("#location_panel").hide();
}


function showOrderDetail(order_id){
    //alert('showOrderDetail');
    getOrderDetail(order_id);

    $("#view_order_detail").show();
    $("#view_order_detail_bg").show();
    $("#view_order_detail").animate({top:'0'});
    $("#view_order_detail_bg").animate({opacity:'0.9'});

    $("#footermenu").hide();
}

function hideOrderDetail(){
    //alert('hideOrderDetail');

    $("#view_order_detail_bg").animate({opacity:'0'});
    $("#view_order_detail").animate({top:'-100%'});
    $("#view_order_detail_bg").hide();
    $("#view_order_detail").hide();

    $("#footermenu").show();
}

function getOrderDetail(order_id){

    $.ajax({
        type : 'POST',
        //url : apiurl+'api.php?method=getOrderDetail&uid='+uid+'&customer_id='+customer_id+'&station_id='+station_id+'&language_id='+language_id,
        url : apiurl+'order_detail',
        data : {
            //method : 'getOrderDetail',
            uid : uid,
            id : order_id
        },
        success : function (response , status , xhr){
            if(response){
                //var orderDetail = eval(response);
                var orderDetail = $.parseJSON(response);

                //$.each(orderDetail, function(index, value){
                //html =+ value.info.order_id;
                //});
                $('#vieworder_id').html('订单编号: '+orderDetail.info.order_id);
                $('#vieworder_order_date').html(orderDetail.info.order_date);
                $('#vieworder_deliver_date').html(orderDetail.info.deliver_date);
                $('#vieworder_shipping_method').html(orderDetail.info.shipping_method);
                $('#vieworder_payment_method').html(orderDetail.info.payment_method);

                $('#vieworder_subtotal').html(orderDetail.info.sub_total);
                $('#vieworder_shipping_fee').html(orderDetail.info.shipping_fee);
                $('#vieworder_total').html(orderDetail.info.total);

                var shipping_info = '<b>送货地址：</b>'+orderDetail.info.shipping_address_1;
                if(orderDetail.info.shipping_code == 'PSPOT'){
                    //shipping_info = '<b>自提点：</b>'+orderDetail.info.ps_name+'('+orderDetail.info.ps_address+')';
                    shipping_info = '<b>自提点：</b>'+orderDetail.info.ps_address;
                }
                $('#vieworder_shipping_info').html(shipping_info);

                var html="";
                $.each(orderDetail.products, function(index, value){
                    html +='<tr>';
                    html += '<td>'+value.name+'</td>';
                    html += '<td>'+parseFloat(value.price).toFixed(2)+'x'+value.quantity+'</td>';
                    html += '<td>'+parseFloat(value.total)+'</td>';
                    html +='</tr>';
                });
                $('#orderproductinsert').html(html);
                $('#vieworder_payment_status').html(orderDetail.info.order_payment_status);

            }
            //alert(limitedProductArr[1]);
            //alert($.inArray('1064',limitedProductArr));
        }
    });
}

function changeLoc(loc,loc_id){
    if(!loc){
        loc = $("#autoUserLoc").html();
        if($("#userLoc").val()){
            loc = "[重新计算]";
            loc += $("#userLoc").val();
        }
    }
    else{
        loc += "[获得对应站点商品列表]";
    }
    $("#autoUserLoc").html(loc);

    hideLocPanel();
}

//检测提交数据完整性
function validation(){
    //Ax20150220:判断订单信息是否填写, 检测手机格式
    var deliverdate = $('#deliver_date').val();
    if(!deliverdate){
        alert('请选择配送日期');
        //$("#name").focus(); //微信中自动激活字段光标效果不好
        return false;
    }

    //console.log($('#shipping_method').val());
    //return false;

    if($('#shipping_method').val() == 1){
//        if(!$('#province').val()){
//            alert('请选择配送区域');
//            return false;
//        }

//        if(!$('#city').val()){
//            alert('请选择配送小区或街道');
//            return false;
//        }

        var userAddress = $('#shipping_address').val();
        if(!userAddress){
            alert('请提供订单配送地址');
            //$("#address").focus();
            return false;
        }
    }

    var credit_pay = $('#credit_pay').val();
    var pay = $('#pay').val();
    if(!credit_pay){
        if(pay==0){
            alert('请选择支付方式');
            return false;
        }
    }

    var userName = $('#shipping_name').val();
    if(!userName){
        alert('请提供订单联系人信息');
        //$("#name").focus(); //微信中自动激活字段光标效果不好
        return false;
    }

    var isMobile=/^(?:13\d|15\d|17\d|18\d|19\d)\d{5}(\d{3}|\*{3})$/; //手机号码验证规则
    var phone = $("#shipping_phone").val();
    if(!isMobile.test(phone)){ //如果用户输入的值不同时满足手机号和座机号的正则
        alert("请正确填写电话号码，例如:18616551234");
        //$("#phone").focus();
        return false;
    }


    submitOrder(); // On wemall.js
}

//购物车两步结算
function goCartPage(){
    $('#infoForm').hide();
    $('#cartlist').show();
}

function goCheckoutPage(){
    //Ax20150220:判断购物车是否有商品
    if($('#ullist li').size()==0){
        alert('!购物车还没有商品，请继续购物吧');
        return false;
    }

    //进入结算页面前，重新计算购物车
    var tmp = reCalcOrder();
    console.log(tmp);

    //进入结算页面，判断余额和订单金额
//    $('#infoForm').show();
//    $('#cartlist').hide();

    var order_total = parseFloat($('#order_total').html());
    if(credit > 0){
        $('#use_credit').show();
        $('#choose_credit').addClass('checked');
        $('#credit_pay').val(1);

        $('#checkout_use_credit').show();
    }
    else{
        $('#use_credit').hide();
        $('#choose_credit').removeClass('checked');
        $('#credit_pay').val(0);

        $('#checkout_use_credit').hide();
    }

    if(order_total >= credit){
        $('#choose_payment').show();
        //changePayment(1);
    }
    else{
        $('#choose_payment').hide();
        changePayment(0);
    }

    //TODO, get check out page content, here only for log
    $.ajax({
        type : 'POST',
        //url : apiurl+'api.php?method=getCheckoutPage&uid='+uid+'&customer_id='+customer_id+'&station_id='+station_id+'&language_id='+language_id,
        url  : apiurl+'checkout',
        data : {
            //method : 'getCheckoutPage',
            uid : uid,
            id : customer_id
        },
        success : function (response , status , xhr){
            if(response){
                return;
            }
        }
    });
}

function changePayment(val){
    //TODO 切换付款方式

    $('#pay').val(val);

    $('#choose_payment_1').removeClass("selected");
    $('#choose_payment_2').removeClass("selected");
    $('#choose_payment_3').removeClass("selected");

    if(val > 0){
        var payment = '#choose_payment_'+val;
        $(payment).addClass("selected");
    }

}

function changeShippingDate(val){
    //TODO 配送日期切换方式
    thisdate = "#shippingdate_"+val;
    choosedate = "#choose_date_"+val;

    $('#deliver_date').val($(thisdate).html());
    //$('#choose_date').find('div[class=the_radio]').removeClass("selected");

    $('#choose_date_1').removeClass("selected");
    $('#choose_date_2').removeClass("selected");
    $('#choose_date_3').removeClass("selected");
    $(choosedate).addClass("selected");

    //console.log($('#deliver_date').val());
}


function changeShippingMethod(val){

    //var thisshippingmethod = "#shipping_method_"+val;
    //TODO 切换配送方式
    //console.log($(thisshippingmethod).html())

    $('#shipping_method').val(val);

    if(val==0){
        $('#show_pickupspot').show();
        $('#show_address').hide();

        $('#shipping_method_0').addClass("selected");
        $('#shipping_method_1').removeClass("selected");
    }
    else{
        $('#show_pickupspot').hide();
        $('#show_address').show();

        $('#shipping_method_0').removeClass("selected");
        $('#shipping_method_1').addClass("selected");
    }

    reCalcTotal();
}

function useCredit(){
    var usecredit = parseInt($('#credit_pay').val());
    var order_total = parseFloat($('#order_total').html());

    if(usecredit == 1)
    {
        $('#choose_credit').removeClass('checked');
        $('#credit_pay').val(0);

        //显示支付方式
        $('#choose_payment').show();
        //changePayment(1);

        //切换Checkout余额支付项
        $('#checkout_use_credit').hide();
    }
    else{
        $('#choose_credit').addClass('checked');
        $('#credit_pay').val(1);

        //余额大于订单金额，隐藏其他支付方式
        if(credit >= order_total){
            $('#choose_payment').hide();
            changePayment(0);
        }

        $('#checkout_use_credit').show();
    }

    reCalcTotal();
}

function reCalcOrder(){
    //Re-calc
    var itemNum = 0;
    var itemPrice = 0;
    var cartCount = 0;
    var totalCount = 0;
    var itemid = 0;
    var name = '';

    var cartItemArr = new Array();

    $('#ullist li').each(function () {
        //TODO: Get actual product price
        itemNum = parseInt($(this).find('span[name=cartitem_count]').html());
        itemPrice = parseFloat($(this).find('span[name=cartitem_price]').html());
        itemid = parseInt($(this).find('span[name=cartitem_id]').html());
        name = $(this).find('span[name=cartitem_title]').html();

        cartItemArr.push(itemid);


        //Error & exit
        if(itemNum < 0){
            clearCache();
            alert('购物车商品金额错误');
            return false;
        }

        cartCount += itemNum;
        totalCount += itemNum*itemPrice;

    });

    //检查商品限购
    //TODO 检查商品金额

    var recalc;

    $.ajax({
        type : 'POST',
        //url : apiurl+'api.php?method=reCalcOrder&uid='+uid+'&customer_id='+customer_id+'&station_id='+station_id+'&language_id='+language_id,
        url : apiurl+'order_recalc',
        async : false,
        cache: false,
        data : {
            //method : 'reCalcOrder',
            uid : uid,
            timeout : 3000, //set timeout
            id : customer_id,
            order_items : cartItemArr
        },
        success : function (response , status , xhr){

            if(response){
                recalc = $.parseJSON(response); //For JSON String
            }
            else{
                alert('提交信息错误，请退出重新访问或与我们联系');
                return false;
            }
        },
        error : function(XMLHttpRequest, textStatus, errorThrown) {
            //alert(XMLHttpRequest.status);
            //alert(XMLHttpRequest.readyState);
            //alert(textStatus);
            alert('服务器繁忙，请稍后重试');
            return false;
        },
        complete : function(){
            //console.log(recalc);
            if(recalc && recalc.alert){
                alert(recalc.message);
                return false;
            }
            else{
                $('#infoForm').show();
                $('#cartlist').hide();
            }
        }
    });

    //购物总额为负数，出错并退出
    if(totalCount<0){
        clearCache();
        alert('购物车商品金额错误');
        return false;
    }

    //重新设置购物车合计提交值
    $('#totalNum').html( cartCount );
    $('#cartN2').html( cartCount );
    $('#totalPrice').html( totalCount.toFixed(2));

    //重新计算订单金额提交值
    reCalcTotal();

    return true;
    //TODO 提交订单前再次计算，保存商品到数据库
}

function reCalcTotal(){
    //TODO: Get Shipping Fee from API
    var lowest = 0;
    var shipping_fee = 3;
    var shipping_method = $('#shipping_method').val(); //配送方式
    var pay = $('#pay').val(); //支付方式


    if(shipping_method==0){
        lowest = 5;
        shipping_fee = 3;
    }
    else{
        lowest = 30;
        shipping_fee = 5;
    }

    var totalPrice = parseFloat($('#totalPrice').html());
    var discount_fee = parseFloat(0); //TODO, 默认优惠为零

    var sub_total = parseFloat(0);
    var order_total = parseFloat(0);
    var use_credit_amount = parseFloat(0);

    $('#cart_total').html(totalPrice.toFixed(2));
    $('#discount_fee').html(discount_fee.toFixed(2));

    if(totalPrice < lowest){
        sub_total = totalPrice + shipping_fee + order_total;
    }
    else{
        shipping_fee = parseFloat(0);
        sub_total = totalPrice + discount_fee;
    }

    var usecredit = parseInt($('#credit_pay').val());
    order_total = sub_total;
    if(usecredit){
        if(sub_total >= credit){
            use_credit_amount = credit;
        }
        else{
            use_credit_amount = sub_total;
        }
    }

    order_total = sub_total-use_credit_amount;

    $('#shipping_fee').html(shipping_fee.toFixed(2));
    $('#sub_total').html(sub_total.toFixed(2));
    $('#use_credit_amount').html(use_credit_amount.toFixed(2));
    $('#order_total').html(order_total.toFixed(2));


    //设置表单提交值
    $('#submit_shipping_fee').val(shipping_fee.toFixed(2));
    $('#submit_discount_fee').val(discount_fee.toFixed(2));
    $('#submit_sub_total').val(totalPrice.toFixed(2));
    $('#submit_order_total').val(order_total.toFixed(2));

    //0元自提订单，设定支付方式为免费

    if(shipping_method==0){
        if(order_total.toFixed(2)==0){  //自提且0元订单，支付方式为免费[3]，只显示3，隐藏微信支付和货到付款
            changePayment(3);
            $('#choose_payment_1').hide();
            $('#choose_payment_2').hide();
            $('#choose_payment_3').show();
        }
        else{ //否则改为微信支付，并只显示微信支付
            changePayment(1);
            $('#choose_payment_1').show();
            $('#choose_payment_2').hide();
            $('#choose_payment_3').hide();
        }

        changePickupSpot($('#pickupspot_id').val());
    }
    else{
        if(pay==3){ //非自提支付方式为免费[3]，改为微信支付，隐藏3，显示微信支付和货到付款
            changePayment(1);
        }
        $('#choose_payment_1').show();
        $('#choose_payment_2').show();
        $('#choose_payment_3').hide();
    }

}

function getProducts(id){
    var loadmenu = '#loadmenu_'+id;

    if($(loadmenu).length > 0){
        return;
    }
    else{
        //Get limited products
        var limitedProductArr = getLimitedProduct();

        $.ajax({
            type : 'POST',
            //url : apiurl+'api.php?method=getCategoryProduct&uid='+uid+'&customer_id='+customer_id+'&station_id='+station_id+'&language_id='+language_id,
            url  : apiurl+'sku_category',
            data : {
                //method : 'getCategoryProduct',
                uid : uid,
                id : id
            },
            success : function(response , status , xhr){
                //$('#product').show();
                //var json = response;
                var json = eval(response);

                var productHtml = '';

                $.each(json, function(index, value){
                    var onsale_tag = '';
                    var onsle_tag_price = '';
                    var product_abstract = '';

                    //Filter limited product
                    if($.inArray(value.product_id,limitedProductArr) >=0 ){
                        return true; //Continue to next loop;
                    }

                    if(value.price > value.special_price){
                        onsale_tag = '<span class="onsale"><i>特价》</i></span>';
                        onsle_tag_price = '<del>'+value.price+'</del>';
                    }

                    if(value.abstract !== ''){
                        product_abstract = ' <span class="product_abstract"><i>'+value.abstract+'</i></span>';
                    }

                    productHtml += '<dd parent="'+value.parent_id+'" menu="'+value.category_id+'" id="loadmenu_'+id+'" class="product_'+value.product_id+'">';
                    productHtml +=      '<div class="tupian">';
                    productHtml +=      '<img class="productimage" data-original="'+imgpath+value.image+'" src="/static/image/lazyload.jpg" style="height:4em; width:4em">';
                    productHtml +=          '<p class="dish2">'+onsale_tag+value.name+'</p>';
                    productHtml +=          '<p class="price2">'+value.special_price+'元/'+value.unit_amount+value.unit_title+'</p>';
                    productHtml +=          '<p>'+onsle_tag_price+product_abstract+'</p>';
                    productHtml +=      '</div>';
                    productHtml +=      '<div class="listproductadd" id="listproductadd_'+value.product_id+'" style="display: block; right:0px;">';
                    productHtml +=          '<a href="javascript:doProduct(\''+ value.product_id+'\',\''+value.name+'\',\''+value.special_price+'\',\''+value.price+'\');" id="'+value.product_id+'" class="reduce"><b class="ico_reduce_start">-</b></a>';
                    productHtml +=      '</div>';

                    productHtml +=      '<div id="listproductchange_'+value.product_id+'" class="orderchange" style="display: none; right:-200px">';
                    productHtml +=          '<a href="javascript:addProductN(\''+ value.product_id+'\',\''+value.special_price+'\');" class="increase"><b class="ico_increase">+</b></a>';
                    productHtml +=          '<span name="cartitem_count" class="count" id="listproductnum_'+value.product_id+'">0</span>';
                    productHtml +=          '<a href="javascript:reduceProductN(\''+ value.product_id+'\',\''+value.special_price+'\');" class="reduce"><b class="ico_reduce">-</b></a>';
                    productHtml +=      '</div>';
                    productHtml += '</dd>';

                });

                //$('#productlistinsert').empty();
                $('#productlistinsert').append( productHtml );

                //Alex: 2015-04-12, Use lazy load to load product images
                var menuimgloc = '#loadmenu_'+id+' .productimage';
                $(menuimgloc).lazyload({effect:"fadeIn", threshold:200});

                //$('.listproductadd').show();
            },
            beforeSend : function(){
                $('#product-load').show();
            },
            complete : function(){
                $('#product-load').hide();
            }
        });
    }
}

function getLimitedProduct(){
    var limitedProduct = '';
    var limitedProductArr = new Array();
    //Get Customer Limited Product
    $.ajax({
        type : 'POST',
        async : false,
        cache: false,
        //url : apiurl+'api.php?method=getCustomerLimitedProductId&uid='+uid+'&customer_id='+customer_id+'&station_id='+station_id+'&language_id='+language_id,
        url : apiurl+'customer_limit_id',
        data : {
            //method : 'getCustomerLimitedProductId',
            uid : uid,
            id : customer_id,
            station_id : station_id
        },
        success : function (response , status , xhr){
            if(response){
                limitedProduct = eval(response);

                $.each(limitedProduct, function(index, value){
                    limitedProductArr.push(value.product_id);
                });
            }
            //console.log('Step1-'+limitedProductArr);
            //alert(limitedProductArr[1]);
            //alert($.inArray('1064',limitedProductArr));
        }
    });

    //console.log('Step2-'+limitedProductArr);
    return limitedProductArr;
}

function changePickupSpot(val){

    $('.pickupspot_address').hide();

    if(val > 0){
        var pickupspot = '#pickupspot_address_'+val;
        $(pickupspot).show();
    }
}