var avgHighLow = [0, 0, 0, 0];
var avgExtremeTemp = [0, 0, 0, 0];

function initializeSliders(cities) {
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
            '50%': 200000,
            '70%': 500000,
            '90%': 5000000,
            'max': 9000000
        }
    });

    pop_slider.noUiSlider.on('update', function(values, handle) {
        var value = values[handle];
        var low_bound = pop_slider.previousElementSibling;
        var high_bound = pop_slider.nextElementSibling;
        var setting_high = handle === 1;
        if (setting_high) {
            high_bound.textContent = Math.round(value);
        } else {
            low_bound.textContent = Math.round(value);
        }

        updateList({'population': [low_bound.textContent, high_bound.textContent]})
    });

    function updateList(change) {
        console.log(change);
        console.log(cities.responseJSON);
        var list = $('.city_list');
        var filteredCities = $.grep(cities.responseJSON, function( city, i ) {
            return city.population > change.population[0] && city.population < change.population[1];
        });
        list.empty();
        $.each(filteredCities, function( i, city ) {
            var city_item = $('<li></li>').text(city.name + ' ' + city.population);
            list.append(city_item);
        })
    }
// End initialize sliders
}



function initializeListAndSliders() {

    cities =  $.getJSON('cities.json', function(response) {
//                console.log(response);
        $.each(response, function(i, city) {
            var city_item = $('<li></li>').text(city.name + ' ' + city.population);
            $('.city_list').append(city_item);
        });
        initializeSliders(cities);
    });
}

var cities;
initializeListAndSliders();

