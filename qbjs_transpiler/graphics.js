// import { playQB64 } from "./r3";

var canvas;
var ctx;
var row, col;
var MAX_ROWS = 25;
var MAX_COLS = 80;

var key_pressed;

var ox, oy;
var x1, x2, y1, y2;
var ii = 0;


document.addEventListener('keypress', event => key_pressed = event.key);
document.addEventListener('DOMContentLoaded', initialize);


function initialize() {
    canvas = document.getElementById("myCanvas");
    ctx = canvas.getContext('2d');
    ctx.font = "30px Courier New";
    ctx.lineWidth = 0.1;
    
    row = 1;
    col = 1;
    // Used for input function
    // char_typed = null;
    typed = false;
    // Used for line function
    ox = 0;
    oy = 0;

    screen(12);
    set_window(-10, -10, 10, 10);
    ctx.fillStyle = "white";
}


// Remember, canvas by default has (0,0) in top left w/ positive y-axis going down
function set_window(nx1, ny1, nx2, ny2) {  // Can't name it window, conflicts with window variable
    // Get bottom left and top right corners
    [x1,y1,x2,y2] = [Math.min(nx1,nx2), Math.min(ny1,ny2), Math.max(nx1,nx2), Math.max(ny1,ny2)];
    // This is annoying
    ctx.setTransform(canvas.width/(x2-x1),0,0,canvas.height/(y1-y2),canvas.width*(0-x1)/(x2-x1),canvas.height*(y2)/(y2-y1));
    // Reset font size
    ctx.font = (y2-y1) / MAX_ROWS + "px Lucida Console";
}


function cls() {
    // Get current values
    var current_matrix = ctx.getTransform();
    var c = ctx.fillStyle;

    // Clear by reverting back and replacing black screen and resetting everything
    ctx.setTransform(1,0,0,1,0,0);
    ctx.fillStyle = "black";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    row = col = 1;
    
    // Set values back to original values from beginning
    ctx.fillStyle = c;
    ctx.setTransform(current_matrix);
}


// Number currently has no use
function screen(number) {
    cls();
}


function print(...expressions) {
    // Window rn always make y-axis positive values go up, so have to make it
    // go down like it usually does or else text is drawn backwards
    ctx.scale(1,-1);

    // Loop through each argument
    for (var expr of expressions) {
        if (expr == ';') {
            continue;
        } else if (expr == ',') {
            if (col >= 56) {
                row++;
                col = 1;
            } else {
                var col_to_goto = 1;
                while (col_to_goto <= col) {
                    col_to_goto += 14;
                }
                col = col_to_goto;
            }
        } else {
            ctx.save();
            tmp = [x1,x2];

            var char_width = ctx.measureText(expr).width / expr.length;
            new_scale = (x2-x1) / (char_width * 80);
            ctx.scale(new_scale, 1);
            [x1, x2] = [x1/new_scale, x2/new_scale];

            var x = x1 + (x2-x1)*col/MAX_COLS;
            var y = y1 + (y2-y1)*row/MAX_ROWS;
            console.log(x, y);
            ctx.fillText(expr, x, y);

            if (col == MAX_COLS) {
                row++;
                col = 1;
            } else {
                col++;
            }

            ctx.restore();
            [x1,x2] = tmp;
        }
    }

    if (expr != ';') {
        row++;
        col = 1;
    }

    // Revert scale back
    ctx.scale(1,-1);
}


function clear_char(text) {
    color('black');
    col -= col <= 0 ? 0 : 1;
    print(text, ';');  // ';' make it not add a newline
    color('white');
    col--;  // print always increments col at the end
}


// let pattern = RegExp(/[\w \.\\,-\/#!$%\^&\*;:{}=\-_`~()@\+\?><\[\]\+]/);
function input(same_line, question_mark, prompt, num_variables) {
    if (question_mark) {
        prompt += '? ';
	}
    
    if (same_line) {
        print(prompt, ';');
    } else {
        print(prompt);
    }
    
    handleInput(num_variables)
    .then((user_input) => {
        row++;
        col = 1;
        return user_input.split(',');
    });
}


async function handleInput(num_variables) {
    var user_input = '';
    var comma_count = 0;
    var typing = true;
    
    while (typing) {
        let char_typed = await new Promise(resolve => document.onkeydown = event => resolve(event.key));;

        if (char_typed == 'Enter' && comma_count >= num_variables-1) {
            typing = false;

        } else if (char_typed == 'Backspace' || char_typed == 'Delete') {
            let n = user_input.length;
            let prev = user_input.substring(n-1, n);
            clear_char(prev);
            user_input = user_input.substring(0, n-1);
            comma_count -= prev == ',' ? 1 : 0;

        } else if (char_typed.length == 1) {
            if (char_typed == ',') {
                if (comma_count >= num_variables-1) {
                    return;
                } else {
                    comma_count += 1;
                }
            }
            print(char_typed, ';');
            user_input += char_typed;
        }
    }

    return user_input;
}


function locate(r, c = 0) {
    row = r >= 1 && r <= MAX_ROWS ? r : row;
    col = c != 'null' && c >= 1 && c <= MAX_COLS ? c : col;
}


function inkeys() {
    ii++;
    console.log(key_pressed);
    return key_pressed;
    // return key_pressed;
}


function color(c) {
    ctx.fillStyle = ctx.strokeStyle = c;
}


function dim(...sizes) {
    var arr = Array(sizes.pop()+1); // +1 bc qb64 indexes from 1 and I don't wanna deal with changing that
    for (let size of sizes.reverse()) {
        var new_arr = Array(size+1);
        for (var i = 0; i < new_arr.length; i++) {
            new_arr[i] = JSON.parse(JSON.stringify(arr));  // This creates a deep copy
        }
        arr = new_arr;
    }
    return arr;
}


function pset(x, y, color) {
    ctx.beginPath();
    color = map_color(color);
    if (color != null) {
        ctx.strokeStyle = color;
        ctx.fillStyle = color;
    }
    pxWidth = (x2-x1)/canvas.width;  // 1 pixel width and height
    pxHeight = (y2-y1)/canvas.height;
    ctx.fillRect(x, y, pxWidth, pxHeight);  // Not center bc it acts kinda weird when it is, isn't colored fully
    ctx.closePath();
}

function circle(x, y, radius, color) {
    ctx.beginPath();
    color = map_color(color);
    if (color != null) {
        ctx.strokeStyle = color;
        ctx.fillStyle = color;
    }
    ctx.arc(x, y, radius, 0, 2*Math.PI);
    ctx.stroke();
    ctx.fill();
    ctx.closePath();
}


function line(coords, color, fill) {
    ctx.beginPath();
    color = map_color(color);
    if (color != null) {
        ctx.strokeStyle = color;
        ctx.fillStyle = color;
    }

    [lx1,ly1,lx2,ly2] = coords.length == 2 ? [ox, oy, ...coords] : [...coords];

    if (fill == null) {
        ctx.moveTo(lx1,ly1);
        ctx.lineTo(lx2,ly2);
        ctx.stroke();
    } else if (fill == "B") {
        ctx.strokeRect(Math.min(lx1,lx2), Math.max(ly1,ly2), Math.abs(lx2-lx1), Math.abs(ly2-ly1)); // if B
    } else if (fill == "BF") {
        ctx.fillRect(Math.min(lx1,lx2), Math.max(ly1,ly2), Math.abs(lx2-lx1), Math.abs(ly2-ly1));   // if BF
    }
    ox = lx2;
    oy = ly2;

    ctx.closePath();
}


function ucase(s) {
    return s.toUpperCase();
}
function mid(s, start, end=-1) {
    return end == -1 ? s.substring(start-1) : s.substring(start-1, end);
}
function len(s) {
    return s.length;
}


function map_color(color) {
    var colors = {
        "0": "rgb(0, 0, 0)",
        "1": "rgb(0, 0, 170)",
        "2": "rgb(0, 170, 0)",
        "3": "rgb(0, 170, 170)",
        "4": "rgb(170, 0, 0)",
        "5": "rgb(170, 0, 170)",
        "6": "rgb(170, 85, 0)",
        "7": "rgb(170, 170, 170)",
        "8": "rgb(85, 85, 85)",
        "9": "rgb(85, 85, 255)",
        "10": "rgb(85, 255, 85)",
        "11": "rgb(85, 255, 255)",
        "12": "rgb(255, 85, 85)",
        "13": "rgb(255, 85, 255)",
        "14": "rgb(255, 255, 85)",
        "15": "rgb(255, 255, 255)"
    };
    return color == null ? null : colors[color];
}

// export { set_window, print, input, locate, inkeys, color, cls, dim, pset, circle, line, screen, ucase, mid, len };