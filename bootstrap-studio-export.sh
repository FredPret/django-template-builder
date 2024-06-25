# put this script in your Bootstrap Studio export folder; make it executable and give it to Bootstrap Studio to run after exporting your page

#!/bin/bash
django_template_directory="/path/to/your/django/template/dir"
static_file_directory="/path/to/where/your/assets/are"
chart_json_path="/path/to/your/chart/variables/json/is"
log_path="/path/to/your/log/file"

echo "$(date +'%Y-%m-%d %H:%M:%S'): Starting script in directory $1" >> $log_path

# move assets
cd $1
rsync -av assets/* "$static_file_directory"
echo "$(date +'%Y-%m-%d %H:%M:%S'): rsync from $1/assets/* to $static_file_directory done" >> $log_path

# move HTML files
cd $1
rsync -av *.html "$django_template_directory"
echo "$(date +'%Y-%m-%d %H:%M:%S'): rsync from $1/*.html to $django_template_directory done" >> $log_path

# run processing script
cd $django_template_directory

# set up command 
command="python create-django-template.py -d $django_template_directory"

# check if a chart json path was specified
if [ -z "$chart_json_path" ]; then
    # chart_json_path is empty; leave command as is
    echo "$(date +'%Y-%m-%d %H:%M:%S'): no chart json path" >> $log_path
else
    # chart json path specified
    echo "$(date +'%Y-%m-%d %H:%M:%S'): chart json path: $chart_json_path" >> $log_path
    command+=" -c $chart_json_path"
fi

# check if static file path = template_path + '/assets' (the default config) or if it's hosted elsewhere (like through Nginx)
if [ "$static_file_directory"=="$django_template_directory/assets" ]; then
    echo "$(date +'%Y-%m-%d %H:%M:%S'): static files in root directory" >> $log_path
else
    echo "$(date +'%Y-%m-%d %H:%M:%S'): static file dir: $static_file_directory " >> $log_path
    command+=" -a"
fi

# run command to process HTML files
python_output=$(eval $command)
echo "$python_output" >> $log_path

# run command to minify CSS and JS files
command="/usr/local/bin/python /Users/fred/localdev/django-template-builder/create-django-template.py -sd $static_file_directory"
python_output=$(eval $command)
echo "$python_output" >> $log_path


echo "$(date +'%Y-%m-%d %H:%M:%S'): python template update complete" >> $log_path
