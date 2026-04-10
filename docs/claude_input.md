## Feature / image converter
### Description
This is a separate script not related to bing wallpaper. It should be placed in a ./scripts directory.
But we could look up some of the code from bing wallpaper to convert images.

### User story
I would like to rent out room in my house. for that I got some images which I need to reformat from dng, heic or any other format to jpeg format. Using a better compression (smaller file size) and easier to display on the web sites. The web sites I will be advertizing are Zillow.com, apartments.com and possibly local Facebook group.
- investigate what file formats, file sizes, and dimensions are required for these web sites. We should use those as default for our script.

### Technical requirements
- I would like to create a a simple python script which converts images to jpeg format
- resizes images for the web sites
- script should have following parameters: input directory, output directory, quality, resize dimensions
- if one of the inline parameters is not provided, the script should take the default parameters, which we still need to discover from above point
- script should be able to handle multiple files at once
- script should be able to handle different file formats
- script should be able to handle different file sizes
- script should be able to handle different file names
- script should be able to handle different file extensions
Script should be able to handle different file names and extensions. The names of the files should be the same as the output directory. Following format:
<yyyymmdd>_<hhmmss>_<output_directory_name>_<counter>.jpg, where counter is a number which is incremented for each file in the output directory. example: 20240101_120000_MyHouse_001.jpg, 20240101_120000_MyHouse_002.jpg, etc.

For the image conversion we could use the following libraries: pillow, opencv, or pyheif. We should investigate which one is the best for this task. To process images faster we could use the observer pattern using the reactivex library. See example:
src/abk_bwp/bingwallpaper.py function _download_images on line 528.

### parameters addition
-i <input directory>
-o <output directory>
-q <jpeg image quality> - basically inverse of compression. 100 is the best quality, 1 is the worst quality.
-s <size of the image> - should be in the format of widthxheight, example: 1920x1080
-h <help>

Use "pydngconverter" library to convert dng files to jpeg. Also use "PyExifTool", to get the date and time of the image.
Thew files should be ordered by date and time. See project /Users/abk/dev/git/eir for more examples.

### Common
Also please use the dev-guidance: /Users/abk/.claude/skills/dev-guidelines/SKILL.md when creating a plan

-------- 8< -------- cut -------- 8< -------- cut -------- 8< -------- cut --------
