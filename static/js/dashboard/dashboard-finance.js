/*
Template Name: Influence Admin Template
Author: jitu
Email: chauhanjitu3@gmail.com
File: js
*/
$(function() {
    "use strict";
    
    // ============================================================== 
    // Revenue Cards
    // ============================================================== 
    
    var url="/dashboard/getsparkdata";
    var csrftoken = $('meta[name=csrf-token]').attr('content');
    var inTransactionData = [];
    var outTransactionData = [];
    var income = [];
    var stockData = [];
    $.ajax({
        type: "POST",
        cache: false,
        url: url,
        headers: {
            "X-CSRFToken": csrftoken,
        },
        dataType: "json",
        success: function(data) {
            if(data.status=='success'){
                $.each(data.inTransactionData, function(i){
                    inTransactionData.unshift(data.inTransactionData[i][0]);
                });
                $.each(data.outTransactionData, function(i){
                    outTransactionData.unshift(data.outTransactionData[i][0]);
                });

                var totalIn = data.totalInOut[0][1];
                var totalOut = data.totalInOut[1][1];
                var totalIncome = totalOut - totalIn;
                var totalProduct = data.totalProduct;

                $(".total_sale .card-body h1").html("$"+numberWithCommas((totalOut).toFixed(2)));
                $(".total_expence .card-body h1").html("$"+numberWithCommas((totalIn).toFixed(2)));
                $(".product_possession .card-body h1").html("$"+numberWithCommas(Number(totalProduct).toFixed(2)));
                $(".profit .card-body h1").html("$"+numberWithCommas((totalIncome).toFixed(2)));

                for(var i = 0 ; i < inTransactionData.length; i++) {
                    var inCash = inTransactionData[i];
                    var outCash = outTransactionData[i];
                    if(inTransactionData[i] == undefined) 
                        inCash = 0;
                    if(outTransactionData[i] == undefined) 
                        outCash = 0;
                    income.push((outCash-inCash).toFixed(2));
                }
                // Display In Transaction Data
                $("#sparkline-revenue").sparkline(outTransactionData, {
                    type: 'line',
                    width: '99.5%',
                    height: '100',
                    lineColor: '#5969ff',
                    fillColor: '',
                    lineWidth: 2,
                    spotColor: undefined,
                    minSpotColor: undefined,
                    maxSpotColor: undefined,
                    highlightSpotColor: undefined,
                    highlightLineColor: undefined,
                    resize:true
                });

                $("#sparkline-revenue2").sparkline(inTransactionData, {
                    type: 'line',
                    width: '99.5%',
                    height: '100',
                    lineColor: '#ff407b',
                    fillColor: '',
                    lineWidth: 2,
                    spotColor: undefined,
                    minSpotColor: undefined,
                    maxSpotColor: undefined,
                    highlightSpotColor: undefined,
                    highlightLineColor: undefined,
                    resize:true
                });
                
                $("#sparkline-revenue3").sparkline([5, 3, 4, 6, 5, 7, 9, 4, 3, 5, 6, 1], {
                    type: 'line',
                    width: '99.5%',
                    height: '100',
                    lineColor: '#25d5f2',
                    fillColor: '',
                    lineWidth: 2,
                    spotColor: undefined,
                    minSpotColor: undefined,
                    maxSpotColor: undefined,
                    highlightSpotColor: undefined,
                    highlightLineColor: undefined,
                    resize:true
                });

                $("#sparkline-revenue4").sparkline(income, {
                    type: 'line',
                    width: '99.5%',
                    height: '100',
                    lineColor: '#ffc750',
                    fillColor: '',
                    lineWidth: 2,
                    spotColor: undefined,
                    minSpotColor: undefined,
                    maxSpotColor: undefined,
                    highlightSpotColor: undefined,
                    highlightLineColor: undefined,
                    resize:true,
                });
                // ============================================================== 
                // Chart Balance Bar
                // ============================================================== 
                var ctx = document.getElementById("chartjs_balance_bar").getContext('2d');
                
                var boxingDay = new Date();
                var prevWeek  = boxingDay*1 - 6*24*3600*1000;
                var result = getDates( prevWeek, boxingDay );
                
                var myChart = new Chart(ctx, {
                    type: 'bar',

                    
                    data: {
                        labels: result,
                        datasets: [{
                            label: 'Purchage Price',
                            data: inTransactionData,
                            backgroundColor: "#66bb6a",
                            borderColor: "#66bb6a",
                            borderWidth:2

                        }, {
                            label: 'Sales Price',
                            data: outTransactionData,
                            backgroundColor: "#ffa726",
                            borderColor: "#ffa726",
                            borderWidth:2


                        }]

                    },
                    options: {
                        legend: {
                                display: true,

                                position: 'bottom',

                                labels: {
                                    fontColor: '#71748d',
                                    fontFamily:'Circular Std Book',
                                    fontSize: 14,
                                }
                        },

                        scales: {
                            xAxes: [{
                                ticks: {
                                    fontSize: 14,
                                    fontFamily:'Circular Std Book',
                                    fontColor: '#71748d',
                                }
                            }],
                            yAxes: [{
                                ticks: {
                                    fontSize: 14,
                                    fontFamily:'Circular Std Book',
                                    fontColor: '#71748d',
                                }
                            }]
                        }
                    }
                });

                // ============================================================== 
                // Gross Profit Margin
                // ============================================================== 
                $(".profit-percent .card-footer .budget").html("$"+numberWithCommas((totalOut).toFixed(2)));
                $(".profit-percent .card-footer .balance").html("$"+numberWithCommas((totalIncome).toFixed(2)));
                Morris.Donut({
                    element: 'morris_gross',

                    data: [
                        { value: ((totalOut*100)/(totalOut+totalIncome)).toFixed(2), label: 'Profit' },
                        { value: ((totalIncome*100)/(totalOut+totalIncome)).toFixed(2), label: '' }
                    
                    ],
                
                    labelColor: '#5969ff',

                    colors: [
                        '#5969ff',
                        '#a8b0ff'
                    
                    ],

                    formatter: function(x) { return x + "%" },
                    resize: true

                });

                // ============================================================== 
                // Net Profit Margin
                // ============================================================== 
                $(".possession-percent .card-footer .budget").html("$"+numberWithCommas((totalIn).toFixed(2)));
                $(".possession-percent .card-footer .balance").html("$"+numberWithCommas((Number(totalProduct)).toFixed(2)));

                Morris.Donut({
                    element: 'morris_profit',

                    data: [
                        // { value: ((totalProduct*100)/(totalIn + totalProduct)).toFixed(2), label: 'Posession' },
                        // { value: ((totalIn*100)/(totalIn + totalProduct)).toFixed(2), label: '' }
                        { value: 89.43, label: 'Posession' },
                        { value: 10.57, label: '' }
                    
                    ],
                
                    labelColor: '#ff407b',


                    colors: [
                        '#ff407b',
                        '#ffd5e1'
                    
                    ],

                    formatter: function(x) { return x + "%" },
                    resize: true

                });

                // ============================================================== 
                //EBIT Morris
                // ============================================================== 
                var ppvp = [];
                var pqvp = [];
                for(var i = 0; i < data.productInfo.length ; i++) {
                    ppvp.push({ x: data.productInfo[i][0], y: data.productInfo[i][2] });
                    pqvp.push({ x: data.productInfo[i][0], y: data.productInfo[i][1] });
                }
                Morris.Bar({
                    element: 'ebit_morris',
                    data: ppvp,
                    xkey: 'x',
                    ykeys: ['y'],
                    labels: ['Y'],
                    barColors: ['#ef5350'],
                    preUnits: ["$"]

                });

                Morris.Bar({
                    element: 'goodservice',
                    data: pqvp,
                    xkey: 'x',
                    ykeys: ['y'],
                    labels: ['Y'],
                    barColors: ['#5969ff'],
                    preUnits: [""]

                });                
                
            }           
        },
        error: function(jqXHR) {
            console.log(jqXHR);
        }
    });

    function numberWithCommas(x) {
        var parts = x.toString().split(".");
        parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
        return parts.join(".");
    }

    function getDates( d1, d2 ){
        var oneDay = 24*3600*1000;
        for (var d=[],ms=d1*1,last=d2*1;ms<=last;ms+=oneDay){
            var date = new Date(ms);
            var month = date.getMonth()+1;
            var day = date.getDate();

            var output = 
                (month<10 ? '0' : '') + month + '-' +
                (day<10 ? '0' : '') + day;
            d.push( output );
            
        }
        return d;
    }
});