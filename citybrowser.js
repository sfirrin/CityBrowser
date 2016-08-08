var avgHighLow = [0, 0, 0, 0];
var avgExtremeTemp = [0, 0, 0, 0];

$('.temp_slider').each(function(i, obj) {
    noUiSlider.create(obj, {
        start: [10, 90],
        connect: true,
        orientation: 'vertical',
        direction: 'rtl',
        range: {
            'min': -20,
            'max': 120
        }
    });

    obj.noUiSlider.on('update', function(values, handle) {

        // Updating the labels for the temp sliders
        var value = values[handle];
        var high_bound = obj.nextElementSibling;
        var low_bound = obj.previousElementSibling;
        var setting_high = handle === 0;
        if (setting_high) {
            high_bound.textContent = Math.round(value);
        } else {
            low_bound.textContent = Math.round(value);
        }

        // Applying the filters to the shown cities



    });
});

var pop_slider = $('#pop_slider')[0];
noUiSlider.create(pop_slider, {
    start: [100000, 10000000],
    connect: true,
    range: {
        'min': 100000,
        'max': 10000000
    }
});


function initiallyPopulate() {
    return $.getJSON('cities.json', function(response) {
//                console.log(response);
        $.each(response, function(i, city) {
            var city_item = $('<li></li>').text(city.name + ' ' + city.population);
            $('.city_list').append(city_item);
        });
    });
}

var cities = initiallyPopulate();

