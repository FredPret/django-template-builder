
from bs4 import BeautifulSoup
import json
import sys
import argparse
import os
from htmlmin import minify
import csscompressor
import rjsmin
import re


def minify_css_and_js_files(root_folder):
    '''
    minifies CSS and JS files in all subfolders of root_folder
    '''
    for subdir, _, files in os.walk(root_folder):
        for file in files:
            # css
            if file.endswith('.css'):
                file_path = os.path.join(subdir, file)
                with open(file_path, 'r') as f:
                    content = f.read()
                minified_content = csscompressor.compress(content)
                with open(file_path, 'w') as f:
                    f.write(minified_content)
            # js
            if file.endswith('.js'):
                file_path = os.path.join(subdir, file)
                with open(file_path, 'r') as f:
                    content = f.read()
                minified_content = rjsmin.jsmin(content)
                with open(file_path, 'w') as f:
                    f.write(minified_content)


def correct_static_file_tag(html, app_name='cms'):
    # load static tag
    html = r'''{% load static %} ''' + html
    # find all file references like assets/..../abc.jpg
    index = 0
    start_text = 'assets/'
    end_text = [' ', '>']
    i = 0
    while index < len(html):
        print(f"hello")
        i += 1
        index = html.find(start_text, index)
        # find endings
        endings = []
        for ending in end_text:
            endings.append(html.find(ending, index))
        end_index = min(endings) # end index is the first ending
        if index != -1 and end_index > index and end_index != -1: # found a snippet - replace it
            # splice new static address into html where the old one was
            old_asset_address = html[index:end_index-1]
            new_asset_address = ''' "{% static '''
            new_asset_address += "'"
            new_asset_address += app_name + '/' + old_asset_address
            new_asset_address += "'"
            new_asset_address += ''' %}" '''
            html = html[:index-1] + new_asset_address + html[end_index:]
            index += len(new_asset_address)
        else:
            break
    return html


def control(html):
    '''
    sets up the most-used django template control structures.

    if:
    django-if="{{ if-statement }} "

    # TODO: django-elif and django-else

    for:
    django-for="iterator"
    django-iterable="iterable"

    :param html:
    :return:
    '''
    soup = BeautifulSoup(html, 'html.parser')

    # django-for
    elements = soup.find_all(attrs={'django-for': True, 'django-iterable': True})
    for element in elements:
        iterator = element['django-for']
        iterable = element['django-iterable']

        # Create new Django for-loop tags
        start_tag = soup.new_tag("span")  # Using 'span' to insert, will replace with actual string later
        start_tag.string = f"{{% for {iterator} in {iterable} %}}"
        end_tag = soup.new_tag("span")
        end_tag.string = "{% endfor %}"

        # Insert the start tag before the element
        element.insert_before(start_tag)
        # Insert the end tag after the element
        element.insert_after(end_tag)

        # remove the 'django-for' and 'django-iterable' attributes
        del element['django-for']
        del element['django-iterable']

    # Convert back to string and replace temporary 'span' tags with for-loop strings
    html = str(soup)
    html = html.replace('<span>{%', '{%').replace('%}</span>', '%}')

    # django-if
    elements = soup.find_all(attrs={'django-if': True})
    for element in elements:
        condition = element['django-if']

        # Create new Django if tags
        start_tag = soup.new_tag("span")  # Using 'span' to insert, will replace with actual string later
        start_tag.string = f"{{% if {condition} %}}"
        end_tag = soup.new_tag("span")
        end_tag.string = "{% endif %}"

        # Insert the start tag before the element
        element.insert_before(start_tag)
        # Insert the end tag after the element
        element.insert_after(end_tag)

        # Optional: Remove the 'django-if' attribute
        del element['django-if']

    # Convert back to string and replace temporary 'span' tags with if statement strings
    html = str(soup)
    html = html.replace('<span>{%', '{%').replace('%}</span>', '%}')
    return html


def blocks(html):
    return html


def variables(html):
    '''
    replace django-variable, django-src, and django-href variables.
    <div django-variable="blabla"></div>
    becomes
    <div>{{ blabla }}</div>

    <element src="..." django-src="123.jpg"/>
    becomes
    <element src="123.jpg"/>

    <element href="..." django-href="123.com"/>
    becomes
    <element href="123.com"/>
    '''
    soup = BeautifulSoup(html, 'html.parser')

    # django-variable
    elements = soup.find_all(attrs={'django-variable': True})
    for element in elements:
        # Replace the content of the <element> with the Django template variable
        element.string = element['django-variable'] #f"{{{{ {element['django-variable']} }}}}"

        # remove the 'django-variable' attribute
        del element['django-variable']

    # django-src
    elements = soup.find_all(attrs={'django-src': True})
    for element in elements:
        # Update the 'src' attribute with the value from 'django-src'
        element['src'] = element['django-src']

        # remove the 'django-src' attribute
        del element['django-src']

    # django-href
    elements = soup.find_all(attrs={'django-href': True})
    for element in elements:
        # Update the 'src' attribute with the value from 'django-src'
        element['href'] = element['django-href']

        # remove the 'django-src' attribute
        del element['django-href']

    # django-year
    elements = soup.find_all(attrs={'django-year': True})
    for element in elements:
        # Replace the content of the <element> with the current year - {% now "Y" %}
        element.string = '''{% now "Y" %}'''

        # remove the 'django-year' attribute
        del element['django-year']

    html = str(soup)
    return html


def update_chart_data(html, chart_selector, data_tag_name, label_tag_name, color_tag_name=None):
    '''
    deletes the sample data in your template chart
    replaces it with Django template tags
    '''
    
    # chart_selector = "sales-per-sku-piechart"
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find the div with the specified class and datasource attribute
    chart_area = soup.find('div', class_="chart-area", attrs={"datasource": chart_selector})
    if not chart_area:
        return None, f"No matching 'chart-area' found. Datasource {chart_selector}"
    
    # Find the canvas tag within this div
    canvas = chart_area.find('canvas', attrs={"data-bss-chart": True})
    if not canvas:
        return None, "No canvas with 'data-bss-chart' found in the specified 'chart-area'"
    
    chart_data = json.loads(canvas['data-bss-chart'].replace('&quot;', '"'))

    if 'data' in chart_data and 'datasets' in chart_data['data'] and chart_data['data']['datasets']:
        # update data
        chart_data['data']['labels'] = 'labeltag'
        chart_data['data']['datasets'][0]['data'] = 'datatag'
        if color_tag_name is not None:
            chart_data['data']['datasets'][0]['data'] = 'colortag'
    else:
        return None, "Chart data format is unexpected"

    # Convert the dictionary back to JSON string
    new_chart_data_string = json.dumps(chart_data)
    
    # Replace old JSON string in the HTML with the new one
    canvas['data-bss-chart'] = new_chart_data_string#.replace('"', '&quot;')

    html = str(soup)
    html = html.replace('"labeltag"', ' ' + str(label_tag_name) + ' ')
    html = html.replace('"datatag"', ' ' + str(data_tag_name) + ' ')
    html = html.replace('"colortag"', ' ' + str(color_tag_name) + ' ')

    return html, None


def main(arg):
    '''
    -d (either d or s is required) template directory with HTML files
    -s (either d or s is required) directory with asset files
    -a (optional) update asset location (for instance /assets/img/hello.jpg) to use a Django tag (like {{ static_root_path }}/img/hello.jpg)
    -c (optional) replace chart data variables
    -f (optional) process given file only, otherwise run through all files in the folder by default
    '''

    # get arguments
    parser = argparse.ArgumentParser(description="Input arguments")
    parser.add_argument('-hd', '--html_directory', type=str, help='Path to template directory')
    parser.add_argument('-sd', '--static_directory', type=str, help='Path to template directory')
    parser.add_argument('-f', '--filename', type=str, help='Process this file only')
    parser.add_argument('-c', '--chart_variable_json_path', type=str, help='Path of chart variable data JSON')
    parser.add_argument('-a', '--update_asset_location', action='store_true', help='Change static asset location to {{ static_root_path }}')
    parsed_args = parser.parse_args(arg)

    # get directory
    if parsed_args.html_directory:
        html_directory = parsed_args.html_directory
        static = False
    else:
        if parsed_args.static_directory:
            static_directory = parsed_args.static_directory
            static = True
        else:
            raise EnvironmentError("Either static_directory (-sd) or html_directory (-hd) must be specified")

    if static:
        # minify css and js
        minify_css_and_js_files(static_directory)
    else:
        # if there's a filename, do that filename only, otherwise list all html files
        if parsed_args.filename:
            file_list = [parsed_args.filename]
        else:
            initial_file_list = os.listdir(html_directory)
            file_list = []
            for file in initial_file_list:
                if file.endswith('.html'):
                    file_list.append(file)

        # if a chart variable json was passed, load it, otherwise ignore the charts
        if parsed_args.chart_variable_json_path:
            chart_variable_json = json.loads(parsed_args.chart_variable_json_path)
        else:
            chart_variable_json = {}
        
        

        # process each html file
        for filename in file_list:
            # open file
            with open(os.path.join(html_directory, filename), 'r') as f:
                html = f.read()

            # update static tag if so instructed
            if parsed_args.update_asset_location:
                html = correct_static_file_tag(html)

            # get chart data for this file - could be nothing
            transformation_list = chart_variable_json.get(filename)

            if transformation_list is not None:
                # replace chart data
                for transformation in transformation_list:
                    chart_selector = transformation['chart_selector']
                    data_tag_name = transformation['data_tag_name']
                    label_tag_name = transformation['label_tag_name']
                    color_tag_name = transformation['color_tag_name']

                    html, error = update_chart_data(html, chart_selector, data_tag_name, label_tag_name, color_tag_name)

                    if error is not None:
                        print(error)
                        sys.exit()

            # control structures
            html = control(html)

            # variable names
            html = variables(html)

            # django blocks
            html = blocks(html)

            # minify html
            html = minify(html)

            # save completed template
            with open(os.path.join(html_directory, filename), 'w') as f:
                f.write(html)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
    