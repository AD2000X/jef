document.addEventListener('DOMContentLoaded', function() {
    // Initialize range sliders
    const ageSlider = document.getElementById('ageSlider');
    noUiSlider.create(ageSlider, {
        start: [18, 87],
        connect: true,
        range: {
            'min': 18,
            'max': 87
        }
    });

    const iqSlider = document.getElementById('iqSlider');
    noUiSlider.create(iqSlider, {
        start: [73, 126],
        connect: true,
        range: {
            'min': 73,
            'max': 126
        }
    });

    // Update display values
    ageSlider.noUiSlider.on('update', function(values) {
        document.getElementById('ageValue').textContent = 
            `Selected range: ${Math.round(values[0])} - ${Math.round(values[1])}`;
    });

    iqSlider.noUiSlider.on('update', function(values) {
        document.getElementById('iqValue').textContent = 
            `Selected range: ${Math.round(values[0])} - ${Math.round(values[1])}`;
    });

    // Calculate button click handler
    document.getElementById('calculateBtn').addEventListener('click', async function() {
        const constructs = ['PL', 'PR', 'ST', 'CT', 'AT', 'EBPM', 'ABPM', 'TBPM', 'AVG'];
        const scores = {};
        
        constructs.forEach(construct => {
            const value = document.getElementById(construct).value;
            if (value !== '') {
                scores[construct] = parseFloat(value);
            }
        });

        const ageRange = ageSlider.noUiSlider.get().map(Number);
        const iqRange = iqSlider.noUiSlider.get().map(Number);

        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    age_range: ageRange,
                    iq_range: iqRange,
                    scores: scores
                })
            });

            const data = await response.json();
            updatePlot(data);
        } catch (error) {
            console.error('Error:', error);
        }
    });

    function updatePlot(data) {
        const constructs = ['PL', 'PR', 'ST', 'CT', 'AT', 'EBPM', 'ABPM', 'TBPM', 'AVG'];
        const zScores = constructs.map(c => data.z_scores[c] || 0);

        const trace = {
            x: constructs,
            y: zScores,
            type: 'bar',
            marker: {
                color: 'rgb(220, 53, 69)'
            }
        };

        const layout = {
            title: 'Z-Scores by Construct',
            shapes: [{
                type: 'line',
                x0: -0.5,
                y0: -2,
                x1: constructs.length - 0.5,
                y1: -2,
                line: {
                    color: 'rgb(0, 123, 255)',
                    width: 2,
                    dash: 'dash'
                }
            }],
            yaxis: {
                title: 'Z-Score',
                range: [-5, 1]
            },
            annotations: [
                {
                    x: 0.95,
                    y: -4.5,
                    xref: 'paper',
                    yref: 'paper',
                    text: `N = ${data.n_samples}<br>Age range: ${data.age_range[0]} - ${data.age_range[1]}<br>IQ range: ${data.iq_range[0]} - ${data.iq_range[1]}`,
                    showarrow: false,
                    align: 'right'
                }
            ]
        };

        Plotly.newPlot('plotDiv', [trace], layout);
    }
});
