function initializeSliders(cities) {
    $('.temp_slider').each(function(i, obj) {
        noUiSlider.create(obj, {
            start: [0, 100],
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
            var high_bound = obj.previousElementSibling;
            var low_bound = obj.nextElementSibling;
            var setting_high = handle === 1;
            if (setting_high) {
                high_bound.textContent = Math.round(value);
            } else {
                low_bound.textContent = Math.round(value);
            }

            // Applying the filters to the shown cities
            var variable = $(obj).closest('.seasons').attr('id');
            var season = $(obj).attr('class').split(' ')[1];
            // console.log(variable + ' ' + season);
            filters[variable][season]= [low_bound.textContent, high_bound.textContent];
            updateList();
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
        filters.population = [low_bound.textContent, high_bound.textContent];
        updateList();
    });

    function updateList() {
        // console.log(cities.responseJSON);
        var list = $('.city_list');
        var filteredCities = $.grep(cities.responseJSON, function( city, i ) {
            var pass = city.population > filters.population[0] && city.population < filters.population[1];
            if (!pass) return false;
            $.each(['spring', 'summer', 'fall', 'winter', 'year'], function(index, season) {
                pass = pass
                    && city['climate']['mean_low'][season] > filters['avg_high_low'][season][0]
                    && city['climate']['mean_high'][season] < filters['avg_high_low'][season][1]
                    && city['climate']['mean_min_low'][season] > filters['extreme_high_low'][season][0]
                    && city['climate']['mean_max_high'][season] < filters['extreme_high_low'][season][1];
            });
            return pass;
        });
        list.empty();
        $.each(filteredCities, function( i, city ) {
            var city_item = $('<li></li>').text(city.name + ' ' + city.population);
            list.append(city_item);
        })
    }
// End initialize sliders
}

var filters = {
    'population': [-100, 999999999],
    'mean_precip': {
        'spring': [-999, 999],
        'summer': [-999, 999],
        'fall': [-999, 999],
        'winter': [-999, 999],
        'year': [-999, 999]
    },
    'avg_high_low': {
        'spring': [-999, 999],
        'summer': [-999, 999],
        'fall': [-999, 999],
        'winter': [-999, 999],
        'year': [-999, 999]
    },
    'extreme_high_low': {
        'spring': [-999, 999],
        'summer': [-999, 999],
        'fall': [-999, 999],
        'winter': [-999, 999],
        'year': [-999, 999]
    },
    'region': ['Northeast', 'South', 'West', 'Southwest', 'Midwest']
};

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

