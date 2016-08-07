// function setColor(){
//
//     // Get the slider values,
//     // stick them together.
//     var color = 'rgb(' +
//         sliders[0].noUiSlider.get() + ',' +
//         sliders[1].noUiSlider.get() + ',' +
//         sliders[2].noUiSlider.get() + ')';
//
//     // Fill the color box.
//     resultElement.style.background = color;
//     resultElement.style.color = color;
// }

var monthsDiv = $('#months');
var resultElement = document.getElementById('result'),
    sliders = document.getElementsByClassName('sliders');

// for (var i = 0; i < 12; i++) {
//     var monthSlider = $('<div></div>').addClass('slider');
//
//     monthsDiv.append(monthSlider);
// }

$('.slider').each(function(i, obj) {
    noUiSlider.create(obj, {
        start: [20, 80],
        connect: true,
        orientation: 'vertical',
        range: {
            'min': 0,
            'max': 100
        }
    });
});

// for ( var i = 0; i < sliders.length; i++ ) {
//
//     noUiSlider.create(sliders[i], {
//         start: 127,
//         connect: "lower",
//         orientation: "vertical",
//         range: {
//             'min': 0,
//             'max': 255
//         },
//         format: wNumb({
//             decimals: 0
//         })
//     });
//
//     // Bind the color changing function
//     // to the slide event.
//     // sliders[i].noUiSlider.on('slide', setColor);
// }

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

