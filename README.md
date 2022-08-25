# QBJS-Transpiler

### Background

My first programming language was [QB64](https://qb64.com/) when my physics teacher taught it to me the summer before my senior year of high school.  I recently worked on creating him a website for his class, and I wanted to add his programs to the website since they were integral to how he taught the course at times.  So, I wrote up this Python script as a small passion project in order to transpile his QB64 code into JavaScript that could run on the website.

### Description

This python program will compile a QB64 program (and hence a QBasic program) into a JS file.  A supplementary [graphics.js](qbjs_transpiler/graphics.js) contains code for various grapihcal functions in the language.  Since JavaScript does not contain functions such as `LINE` or `PSET`, using these requires importing the graphics.js file.  These functions are automatically imported when transpilation is done.  These transpiler will also wrap all of the code in a function called `playQB64()` and export it.  There currently is not functionality to disable these features.

### Usage

To use the transpiler, you must do the following:
1. Download the [qbjs_transpiler folder](qbjs_transpiler).
2. Install python [here](https://www.python.org/downloads/) or using the command for your operating system.
3. Navigate to the directory containing the file inside the qbjs_transpiler folder.
4. Run the [qbjs_transpiler.py](qbjs_transpiler/qbjs_transpiler.py) file with the syntax `python qbjs_transpiler.py <input_filename> <output_filename>`.  Make sure to include the extensions!

### Limitations

**THIS TRANSPILER IS NOT PERFECT!**  There are issues due to the nature in which I have the transpiler go through the code.  Until I recreate a better version, this transpiler may not correctly transpile all of your code, but it will translate most of it.  :)

### Future Steps

This is a beta version.  It works by going line-by-line through the original .bas file and translating it into JavaScript.  Unfortunately, this makes keeping track of the state of the program a headache, and it doesn't account for things shorter than one line, such as correctly transpiling the arguments to a function.  A future version will be written to tackle this using the grammatical trees of the languages.  This will make it much easier to keep track of these things and remove an independence on the format of the original file.  It will also be written in JavaScript to allow for transpiling to take place in the browser.  Furthermore, most of the QB64 language has not been included yet because there are simply so many different commands.  This will be added to in the future.
