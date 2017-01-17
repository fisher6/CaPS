
function sendAnswer(e) {
    var container = $("#exampleDiv")
    console.log(e);
    $.post({
        url: '/tasks/send_response/',
        contentType: 'application/json; charset=utf-8',
        processData: false,
        async: false;
        data: JSON.stringify(e),
    })
    .done(function(data) {
        container.append(data);
    });
}

function getQuestion() {
    var container = $("#exampleDiv")
    $.get("/tasks/get_next_question/")
        .done(function(data) {
            var selections = [];

            var query = JSON.parse(data);
            //console.log(question);
            console.log(query["options"]);

            opts = JSON.parse(query["options"]);
            numOpts = opts.length;
            console.log(numOpts)

            for (i = 0; i < numOpts; i++) {
                var opt = opts[i]["fields"];
                console.log(opt);
                number = opt["number"];
                text = opt["text"]
                container.append(number + " " + text + " ");
                selections.push(number);
            }

            sendAnswer(selections);
        });
}

$(document).ready(function () {
  // Add event-handlers

  // Get initial question
  getQuestion();

  // CSRF set-up copied from Django docs
  function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
  }
  var csrftoken = getCookie('csrftoken');
  $.ajaxSetup({
    beforeSend: function(xhr, settings) {
        xhr.setRequestHeader("X-CSRFToken", csrftoken);
    }
  });
});
