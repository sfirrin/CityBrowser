function initializeSliders(cities) {
    $('.temp_slider').each(function(i, obj) {
        // Make a slider with pips for the year sliders
        if ($(obj).attr('class').split(' ')[1] === 'year') {
            noUiSlider.create(obj, {
                start: [-20, 120],
                connect: true,
                orientation: 'vertical',
                direction: 'rtl',
                step: 2,
                range: {
                    'min': -20,
                    'max': 120
                },
                pips: { // Show a scale with the slider
                    mode: 'values',
                    values: [-20, 0, 20, 40, 60, 80, 100, 120],
                    density: 2
                }
            });
        } else {
            noUiSlider.create(obj, {
                start: [-20, 120],
                connect: true,
                orientation: 'vertical',
                direction: 'rtl',
                step: 2,
                range: {
                    'min': -20,
                    'max': 120
                }
            });
        }


        obj.noUiSlider.on('update', function(values, handle) {

            // Updating the labels for the temp sliders
            var value = values[handle];
            var highBound = obj.previousElementSibling;
            var lowBound = obj.nextElementSibling;



            var setting_high = handle === 1;

            var highChange = setting_high ? value - highBound.textContent : 0;
            var lowChange = setting_high ? 0 : value - lowBound.textContent;

            if (setting_high) {
                highBound.textContent = Math.round(value);
            } else {
                lowBound.textContent = Math.round(value);
            }



            // Applying the filters to the shown cities
            var variable = $(obj).closest('.seasons').attr('id');
            var season = $(obj).attr('class').split(' ')[1];

            var isLocked = $('#' + variable + '_lock').is(':checked');



            if (isLocked && !lockUpdateInProgress) {
                // TODO: Optimize this so it's not super slow
                // Changing the other sliders in this variable
                var variableSliders = $(obj).parent().siblings().children('.temp_slider');
                lockUpdateInProgress = true;
                $.each(variableSliders, function(i, slider) {
                    // console.log(slider);
                    var currentBounds = slider.noUiSlider.get();
                    // console.log('Changes ' + [lowChange, highChange]);
                    // console.log('Current ' + currentBounds);
                    var newLow = +currentBounds[0] + +lowChange;
                    var newHigh = +currentBounds[1] + +highChange;
                    // console.log('New ' + [newLow, newHigh]);
                    slider.noUiSlider.set([newLow, newHigh]);
                });
                lockUpdateInProgress = false;
            }

            // console.log(isLocked);
            // console.log(variable + ' ' + season);
            filters[variable][season]= [lowBound.textContent, highBound.textContent];
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
            '95%': 1000000,
            'max': 9000000
        },
        step: 5000,
        pips: {
            mode: 'positions',
            values: [0, 20, 40, 60, 80, 100],
            density: 2
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

    var rent_slider = $('#rent_slider')[0];
    noUiSlider.create(rent_slider, {
        start: [200, 5000],
        connect: true,
        range: {
            'min': 600,
            'max': 2600
        },
        step: 20,
        pips: {
            mode: 'positions',
            values: [0, 20, 40, 60, 80, 100],
            density: 2
        }
    });

    $.each([pop_slider, rent_slider], function(index, slider) {
        slider.noUiSlider.on('update', function(values, handle) {
            var value = values[handle];
            var low_bound = slider.previousElementSibling;
            var high_bound = slider.nextElementSibling;
            var setting_high = handle === 1;
            if (setting_high) {
                high_bound.textContent = Math.round(value);
            } else {
                low_bound.textContent = Math.round(value);
            }
            if (index === 0) {
                filters.population = [low_bound.textContent, high_bound.textContent];
            } else {
                filters.median_2br_rent = [low_bound.textContent, high_bound.textContent];
            }
            updateList();
        });
    });

    rent_slider.noUiSlider.on('update', function(values, handle) {
        var value = values[handle];
        var low_bound = rent_slider.previousElementSibling;
        var high_bound = rent_slider.nextElementSibling;
        var setting_high = handle === 1;

    });

    function updateList() {
        // console.log(cities.responseJSON);
        var list = $('.city_list');
        var filteredCities = $.grep(cities.responseJSON, function( city, i ) {
            var pass = city.population > filters.population[0] && city.population < filters.population[1]
                && city.median_2br_rent > filters.median_2br_rent[0]
                && city.median_2br_rent < filters.median_2br_rent[1];
            if (!pass) return false;
            $.each(['apr', 'jul', 'oct', 'jan', 'year'], function(index, season) {
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
            var cityDiv = cityDivMap[city.id];
            list.append(cityDiv);
            return i <= 50;
        })
    }
// End initialize sliders
}

function getCityDiv(city) {
    var cityLi = $('<li></li>');
    var cityDiv = $('<div></div>').addClass('row');
    var leftSection = $('<div></div>').addClass('col-xs-3');
    var rightSection = $('<div></div>').addClass('col-xs-9');
    var thumbLinkWrapper = $('<a target="_blank" href="' + city.photo_details_url + '"></a>');
    var thumbContainer = $('<div></div>').addClass('thumb');
    thumbContainer.append($('<img src="city_images/' + city.id + '.jpg" />').addClass('img-responsive'));
    thumbLinkWrapper.append(thumbContainer);
    leftSection.append(thumbLinkWrapper);
    rightSection.append($('<h4></h4>').text(city.name));
    var table = $('<table class="table"></table>');
    var headings = $('<tr></tr>');
    headings.append($('<th>Month</th>'));
    headings.append($('<th>Average high</th>'));
    headings.append($('<th>Average low</th>'));
    headings.append($('<th>Average monthly max</th>'));
    headings.append($('<th>Average monthly min</th>'));
    headings.append($('<th>Precipitation</th>'));
    table.append(headings);
    $.each(['apr', 'jul', 'oct', 'jan', 'year'], function(i, month) {
        var month_row = $('<tr><th>' + month + '</th></tr>');
        $.each(['mean_high', 'mean_low', 'mean_max_high', 'mean_min_low', 'mean_precip'], function(i, stat) {
            month_row.append($('<td>' + city.climate[stat][month] + '</td>'));
        });
        table.append(month_row);
    });

    rightSection.append(table);
    var wiki_info = $('<a target="_blank"></a>').attr('href', city.wiki);
    wiki_info.append($('<p></p>').text(city.wiki_intro));
    rightSection.append(wiki_info);
    cityDiv.append(leftSection, rightSection);

    cityLi.append(cityDiv);
    return cityLi;
}

function getCityDivMap(cities) {
    cityDivMap = {};
    // console.log(cities);
    $.each(cities.responseJSON, function(i, city) {
        // console.log(city.name);
        cityDivMap[city.id] = getCityDiv(city);
    });
}

function initializeListAndSliders() {

    cities =  $.getJSON('cities.json', function(response) {
        getCityDivMap(cities);
        initializeSliders(cities);
    });
}

var filters = {
    'population': [-100, 999999999],
    'median_2br_rent': [-1, 99999],
    'mean_precip': {
        'apr': [-999, 999],
        'jul': [-999, 999],
        'oct': [-999, 999],
        'jan': [-999, 999],
        'year': [-999, 999]
    },
    'avg_high_low': {
        'apr': [-999, 999],
        'jul': [-999, 999],
        'oct': [-999, 999],
        'jan': [-999, 999],
        'year': [-999, 999]
    },
    'extreme_high_low': {
        'apr': [-999, 999],
        'jul': [-999, 999],
        'oct': [-999, 999],
        'jan': [-999, 999],
        'year': [-999, 999]
    },
    'region': ['Northeast', 'South', 'West', 'Southwest', 'Midwest']
};

var lockUpdateInProgress;
var cityDivMap;
var cities;
initializeListAndSliders();

