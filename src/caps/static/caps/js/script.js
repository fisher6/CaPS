var chat_template = 
    '<div id="{{ id }}" class="popup-box chat-popup z-pos-above-1 z-depth-1">' +
    '    <div class="popup-head">' +
    '        <div class="popup-head-left">' +
    '            {{ name }}' +
    '        </div>' +
    '        <div class="popup-head-right">' +
    '            <a href="javascript:close_popup(\'{{ id }}\');">' +
    '                &#10005' +
    '            </a>' +
    '        </div>' +
    '        <div style="clear: both">' +
    '            <!-- Blank -->' +
    '        </div>' +
    '    </div>' +
    '    <div id="popup-messages-{{ id }}" class="popup-messages">' +
    '        <div class="center-align">' +
    '            {{ welcome_message }}' +
    '        </div>' +
    '        <div id="chat-{{ id }}">' +
    '            <!-- Filled in JS -->' +
    '        </div>' +
    '        <form id="message-{{ id }}" action="sendMessage" method="post">' +
    '            <textarea id="textarea-{{ id }}" class="popup-input" rows="3" type="text" name="message" placeholder="Type message here...">' +
                '</textarea>' +
    '            <input class="popup-input-button" type="submit" value="Send">' +
    '        </form>' +
    '    </div>' +
    '</div>';

var emergency_welcome_message = 
    'You are chatting with a trained professional. ' +
    'Everything you say will be kept confidential unless ' +
    'there is an immediate threat to yourself or others.';

var currentUser = '';
    
// The total number of popups that can be displayed based on the viewport width
var total_popups = 0;

// Array of popups ids
var popups = [];

// Current open sockets (same indexing as popups)
var sockets = [];

function updateScroll(element) {
    element.scrollTop = element.scrollHeight;
}

// This function can remove an array element.
Array.remove = function(array, from, to) {
    var rest = array.slice((to || from) + 1 || array.length);
    array.length = from < 0 ? array.length + from : from;
    return array.push.apply(array, rest);
};

// Creates markup for a new popup. Adds the id to popups array.
function register_popup(id, name, currentUser) {
    // Popup already registered.
    for(var i = 0; i < popups.length; i++)
        if(id == popups[i]) 
            return;
    
    if(id == "chat" || id == "emergency" || id == "emergencyresponder" || id == "schedule" || id == "receptionist" ||
       (name.includes("Counselor") && !name.includes("Counselor: Counselor"))
      ) {
        var welcome_message = 
            (id == "emergency") ? emergency_welcome_message : "";

        var chat_window = chat_template.replace(/{{ id }}/g, id);
        chat_window = chat_window.replace(/{{ name }}/g, name);
        chat_window = chat_window.replace(/{{ welcome_message }}/g, welcome_message);
        $("body").append(chat_window);

        $("#" + id + "-button").hide();
        this.currentUser = currentUser;

        //socket = new WebSocket("ws://" + window.location.host + "/" + id);
        socket = new WebSocket("ws://" + window.location.host + "/" + id);
        socket.onmessage = function(event) {
            message = JSON.parse(event.data);
            text = message["text"];
            user = message["user"];
            if (currentUser == user) {
                $("#chat-" + id).append("<p class=\"right-align lite-padded\">" +
                            "<span class=\"chat-username\">" + user + ":" + "</span>" + "<br>" +
                             text + "</p>");

            } else {
            $("#chat-" + id).append("<p class=\"left-align lite-padded\">" +
                                    "<span class=\"chat-username\">" + user + ":" + "</span>" + "<br>" +
                                     text + "</p>");
            }
            updateScroll(document.getElementById("popup-messages-" + id));
        }

        $("#message-" + id).submit(function(event) {
            event.preventDefault();
            for(var i = 0; i < popups.length; i++) {
                if(id == popups[i]){
                    sockets[i].send($("#message-" + id + ">textarea").val());
                    break;
                }
            }
            $("#message-" + id + ">textarea").val("");
        });

        $("#textarea-" + id).keyup(function(event) {
            event.preventDefault();
            if(event.keyCode == 13){
                for(var i = 0; i < popups.length; i++) {
                    if(id == popups[i]){
                        sockets[i].send($("#message-" + id + ">textarea").val());
                        $("#message-" + id + ">textarea").val("");
                        break;
                    }
                }
            }
        });

        popups.push(id);
        sockets.push(socket);
        calculate_popups();
    }
}

// Close a popup
function close_popup(id) {
    for(var i = 0; i < popups.length; i++) {
        if(id == popups[i]){
            sockets[i].close();
            
            Array.remove(popups, i);
            Array.remove(sockets, i);
            
            $("#" + id).remove();
            $("#" + id + "-button").show();
            
            calculate_popups();
            return;
        }
    }
}

// Calculate the total number of popups suitable and then populate the total_popups variable.
function calculate_popups() {
    var width = window.innerWidth;
    if(width < 540) {
        total_popups = 0;
    } else {
        width = width - 200;
        // 320 is width of a single popup box
        total_popups = parseInt(width / 320);
    }
    display_popups();
}

// Displays the popups. Displays based on the maximum number of popups that can be displayed on the current viewport width
function display_popups() {
    var right = 220;

    var i = 0;
    for(i; i < total_popups; i++) {
        if(popups[i] != undefined) {
            var element = document.getElementById(popups[i]);
            element.style.right = right + "px";
            right = right + 320;
            element.style.display = "block";
            updateScroll(document.getElementById("popup-messages-" + popups[i]));
        }
    }

    for(var j = i; j < popups.length; j++) {
        var element = document.getElementById(popups[j]);
        element.style.display = "none";
    }
}

// Recalculate when window is loaded and also when window is resized.
$("document").ready(function() {
    calculate_popups();
    $('.modal-trigger').leanModal({
        dismissible: true
    });
    $(".button-collapse").sideNav();
});
$("document").resize(function() {
    calculate_popups();
});

