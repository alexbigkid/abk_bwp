#!/usr/bin/env bash

PICTURE_DIR="$HOME/Pictures/bingwallpapers"

mkdir -pv $PICTURE_DIR

urls=( $(curl -s https://www.bing.com/?cc=gb | \
	grep -Eo "url:'.*?'" | \
	sed -e "s/url:'\([^']*\)'.*/https:\/\/bing.com\1/" | \
	sed -e "s/\\\//g") )

for p in ${urls[@]}; do
	filename=$(echo $p|sed -e "s/.*\/\(.*\)/\1/")
	if [ ! -f $PICTURE_DIR/$filename ]; then
		echo "Downloading: $filename to $PICTURE_DIR ..."
		curl -Lo "$PICTURE_DIR/$filename" $p
	else
		echo "Skipping: $filename ..."
	fi
done

ImageFilePath=$PICTURE_DIR/$filename

osascript -e 'set theUnixPath to POSIX file "'$ImageFilePath'" as text
              tell application "Finder"
              set desktop picture to {{theUnixPath}} as alias
              end tell'
