function render_price_chart(chart_layout, chart_options) {
    container = document.getElementById("price_chart");
    container.innerHTML = "";

    chart_type = chart_options['type'];
    price_data = chart_options['price_data'];
    ma_line_data = chart_options['ma_line_data'];
    rsi_line_data = chart_options['rsi_line_data'];

    let chart = LightweightCharts.createChart(container, chart_layout);
    let series;
    
    // Default price value
    if (chart_type === "Candlestick") {
        series = chart.addSeries(LightweightCharts.CandlestickSeries, {
            upColor: "#26a69a",
            wickUpColor: "#26a69a",
            downColor: "#ef5350",
            wickDownColor: "#ef5350",
            borderVisible: false,
        },
        0);
    } else {
        series = chart.addSeries(LightweightCharts.LineSeries, {
            color: 'rgba(0, 102, 204, 1)',
            lineWidth: 2,
            priceLineVisible: false,
            lastValueVisible: true,
            crosshairMarkerVisible: true,
            crosshairMarkerRadius: 4,
            crosshairMarkerBorderColor: 'rgba(0, 102, 204, 0.8)',
        }, 
        0);
    }

    series.setData(price_data);

    // MA lines
    if ( Object.keys(ma_line_data).length > 0 ) {
        Object.keys(ma_line_data).forEach(period => {
            ma_series = chart.addSeries(LightweightCharts.LineSeries, {
                color: 'rgba(0, 102, 204, 1)',
                lineWidth: 1,
                priceLineVisible: false,
                lastValueVisible: true,
                crosshairMarkerVisible: true,
                crosshairMarkerRadius: 4,
                crosshairMarkerBorderColor: 'rgba(0, 128, 255, 0.8)',
            });

            ma_series.setData(ma_line_data[period]);
        },
        0);
    }

    // RSI line
    if (rsi_line_data.length > 0) {
        const rsiSeries = chart.addSeries(LightweightCharts.LineSeries, {
            color: '#6E56CF',
            lineWidth: 2,
            priceFormat: {
                type: 'price',
                precision: 2,
            },
            priceScale: 'rsi-scale',
        },
        1                                 
        );
        // Configure the RSI price scale: fixed 0–100
        rsiSeries.priceScale().applyOptions({
            autoScale:   false,
            minValue:    0,
            maxValue:    100,
            borderVisible: false,
        });
        // Draw threshold lines at 70 & 30
        rsiSeries.createPriceLine({
            price:         70,
            color:         '#FFAB00 ',
            lineWidth:     1,
            lineStyle:     LightweightCharts.LineStyle.Dashed,
            axisLabelVisible: true,
        });
        rsiSeries.createPriceLine({
            price:         30,
            color:         '#FF1744',
            lineWidth:     1,
            lineStyle:     LightweightCharts.LineStyle.Dashed,
            axisLabelVisible: true,
        });

        // Split charts
        const totalHeight = container.clientHeight;
        chart.applyOptions({
            panes: [
                { height: totalHeight * 0.7 }, // 70% 
                { height: totalHeight * 0.3 }, // 30%
            ],
        });

        rsiSeries.setData(rsi_line_data);
    }

    chart.timeScale().fitContent();
}