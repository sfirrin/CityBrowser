from jinja2 import Template

def get_weatherbox(city):
    # Takes as input a city dictionary as made in the get_cities function
    # of the cities file
    # Returns a string of a filled weather box in the format of the Wikipedia
    # template found at https://en.wikipedia.org/wiki/Template:Weather_box
    template_string = open('weather_box_template.jinja', 'rb').read().decode('utf-8')
    box_template = Template(template_string)

    print(box_template.render(city))