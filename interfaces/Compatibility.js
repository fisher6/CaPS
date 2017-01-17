function startExercise() {

    var query;
    
    // canvas and drawing variables
    var canvas = document.getElementById("taskCanvas");
    var context = canvas.getContext("2d");
    var quizbg = new Image();
    var mx = 0;
    var my = 0;
    var showNext = false;
    var textPositions = [20, 145, 235, 325, 405, 495];
    var rectPositions = [0, 110, 200, 290, 380, 470, 560]

    // exercise info tracking variables
    var qnumber = 0;
    var quizFinished = false;
    var questions = [];
    var options = [];
    var optionNumbers = [];
    var currQuestion = new String;
    var currOptions = [];
    var currOptionNumbers = [];
    var chosen = [];
    var selectOne = false;
    var begin = true;

    quizbg.onload =
        function(){
            //context.drawImage(quizbg, 0, 0);
            showBeginMessage();
        }

    quizbg.src = "/static/tasks/images/quizbg.png";

    GetLines = function(ctx, text, maxWidth) {
        var words = text.split(" ");
        var lines = [];
        var currentLine = words[0];

        for (var i = 1; i < words.length; i++) {
            var word = words[i];
            var width = ctx.measureText(currentLine + " " + word).width;
            if (width < maxWidth) {
                currentLine += " " + word;
            } else {
                lines.push(currentLine);
                currentLine = word;
            }
        }
        lines.push(currentLine);
        return lines;
    }

    Redraw = function() {
        context.clearRect(0, 0, canvas.width, canvas.height);
        //context.drawImage(quizbg, 0, 0);
        if (!begin) {
            SetQuestions();
            var length = chosen.length;
            for (i = 0; i < length; i++) {
                choice = currOptionNumbers.indexOf(chosen[i]);
                context.drawImage(quizbg, 0, 400, 75, 70, 480, 110 + (90 * choice),
                      75, 70);
            }
        }
    }

    showBeginMessage = function() {
        getProgress();
        if ($("#percentDone").html() == "0%") {
            context.font = "20pt Calibri,Arial";
            context.fillText("Welcome to the Initial Personality Assessment!",
                             20, 100);
            context.font = "16pt Calibri,Arial";
            context.fillText("You will be asked a series of questions to help to ",
                             20, 200);
            context.fillText("determine which of our counselors will be the best fit",
                             20, 220);
            context.fillText("for you.",
                             20, 240);
            context.fillText("Some questions will allow you to choose multiple answers",
                             20, 260);
            context.fillText("while others will not.",
                             20, 280);
            context.fillText("The only people that will see the results of this assessment",
                             20, 310);
            context.fillText("are the receptionist who will help you find the right",
                             20, 330);
            context.fillText("counselor and whichever counselor is assigned to help you.",
                             20, 350);
            context.fillText("You do not have to take this quiz, but it will help us",
                             20, 380);
            context.fillText("match you up with a counselor better.",
                             20, 400);
            context.fillText("Click anywhere to continue.",
                             20, 500);
        }
        else {
            context.font = "20pt Calibri,Arial";
            context.fillText("Welcome back to the", 20, 100);
            context.fillText("Initial Personality Assessment!", 20, 125);
            context.font = "16pt Calibri,Arial";
            context.fillText("You will be asked a series of questions to help to ",
                             20, 200);
            context.fillText("determine which of our counselors will be the best fit",
                             20, 220);
            context.fillText("for you.",
                             20, 240);
            context.fillText("Some questions will allow you to choose multiple answers",
                             20, 260);
            context.fillText("while others will not.",
                             20, 280);
            context.fillText("The only people that will see the results of this assessment",
                             20, 310);
            context.fillText("are the receptionist who will help you find the right",
                             20, 330);
            context.fillText("counselor and whichever counselor is assigned to help you.",
                             20, 350);
            context.fillText("You do not have to take this quiz, but it will help us",
                             20, 380);
            context.fillText("match you up with a counselor better.",
                             20, 400);
            context.fillText("Click anywhere to continue.",
                             20, 500);
        }
    }

    SetQuestions = function() {
        currQuestion = questions[qnumber];
        currOptions = options[qnumber];
        currOptionNumbers = optionNumbers[qnumber];

        selectOne = (currOptions.length <= 2 ||
                     currQuestion.includes("On a scale of"));

        context.textBaseline = "middle";
        context.font = "18pt Calibri,Arial";

        // Find out how many lines of text the question takes up
        // Doesn't support more than 3
        lines = GetLines(context, currQuestion, canvas.width);
        context.globalAlpha = 0.75;
        context.fillStyle="#e0e0e0";
        context.fillRect(0, rectPositions[0], 550, 90);
        context.globalAlpha = 1.0;
        context.fillStyle="#5e0202";
        var length = lines.length;
        if (length == 1) {
            context.fillText(lines[0], 20, textPositions[0] + 25);
        }
        else if (length == 2) {
            context.fillText(lines[0], 20, textPositions[0] + 10);
            context.fillText(lines[1], 20, textPositions[0] + 30);
        }
        else {
            context.fillText(lines[0], 20, textPositions[0]);
            context.fillText(lines[1], 20, textPositions[0] + 20);
            context.fillText(lines[1], 20, textPositions[0] + 40);
        }

        context.font = "14pt Calibri,Arial";

        context.globalAlpha = 0.75;
        context.fillStyle="#e0e0e0";

        // There can be no more than 5 options
        var numOptions = (currOptions.length > 5 ? 5 : currOptions.length);
        for ( var i = 0; i < numOptions; i++ ) {
            context.fillRect(0, rectPositions[i + 1], 550, 70);
        }
        context.globalAlpha = 1.0;
        context.fillStyle="#000000";
        for ( var i = 0; i < numOptions; i++ ) {
            context.fillText(currOptions[i], 20, textPositions[i + 1]);
        }
    }

    canvas.addEventListener('click', ProcessClick, false);

    function ProcessClick(ev) {

        var rect = canvas.getBoundingClientRect();
        var my = event.clientY - rect.top;

        if (ev.y == undefined) {
            my = ev.pageY - canvas.offsetTop;
        }
        else {
            if (begin) {
                Redraw();
                begin = false;
                getQuestionInitial();
            }
            else {
                length = currOptions.length;
                if (my>110 && my<180 && length >= 1) {
                    GetFeedback(0);
                }
                else if (my>200 && my<270  && length >= 2) {
                    GetFeedback(1)
                }
                else if (my>290 && my<360  && length >= 3) {
                    GetFeedback(2);
                }
                else if (my>380 && my<450  && length >= 4) {
                    GetFeedback(3);
                }
                else if (my>470 && my<540  && length >= 5) {
                    GetFeedback(4);
                }
                else if (my>560 && showNext) {
                    ResetQ();
                }
            }
        }
    }

    GetFeedback = function(choice) {
        if (choice < 0 || choice >= currOptionNumbers.length) {
            return;
        }

        numberChoice = currOptionNumbers[choice];
        var index = chosen.indexOf(numberChoice);
        if (index > -1) {
            chosen.splice(index, 1);
            Redraw();
        }
        else {
            if (!selectOne || (selectOne && chosen.length < 1)) {
                chosen.push(numberChoice);
                context.drawImage(quizbg, 0, 400, 75, 70, 480, 110 + (90 * choice),
                  75, 70);
            }
        }

        if (chosen.length >= 1) {
            showNext = true;
            Redraw();
            context.font = "14pt Calibri,Arial";
            context.globalAlpha = 0.75;
            context.fillStyle="#e0e0e0";
            context.fillRect(0, rectPositions[6], 550, 50);
            context.globalAlpha = 1.0;
            context.fillStyle="#000000";
            context.fillText("Click here to continue", 20, 580);
        }
        else {
            showNext = false;
            Redraw();
        }

    }

    ResetQ = function() {
        sendAnswer(chosen);
        chosen = [];
        context.clearRect(0, 0, canvas.width, canvas.height);
    }

    ResetQFinal = function() {
        showNext = false;
        context.clearRect(0, 0, 550, 400);
        qnumber++;
        if (qnumber == questions.length) {
            EndQuiz();
        }
        else {
            //context.drawImage(quizbg, 0, 0);
            SetQuestions();
        }
    }

    EndQuiz = function() {
        canvas.removeEventListener('click', ProcessClick, false);
        //context.drawImage(quizbg, 0, 0, 550, 90, 0, 0, 550, 400);
        context.font = "20pt Calibri,Arial";
        context.fillText("You have finished the compatibility quiz!", 20, 100);
        context.font = "16pt Calibri,Arial";
        context.fillText("Please schedule an appointment by",
                         20, 200);
        context.fillText("calling, chatting on the home page,",
                         20, 220);
        context.fillText("or going to the CaPS building.",
                         20, 240);
        context.fillText("More information is available",
                         20, 270);
        context.fillText("on the contact page.",
                         20, 290);
    }

    getProgress = function() {
        $.get("/tasks/get_progress")
        .done(function(data) {
            percentage = JSON.parse(data)["percentage"].toFixed(2);
            $("#progressBar").css("width", percentage*100 + "%");
            $("#percentDone").html(percentage*100 + " %");
        });
    }

    sendAnswer = function(e) {
        $.post({
            url: '/tasks/send_response',
            contentType: 'application/json; charset=utf-8',
            processData: false,
            data: JSON.stringify(e)
        })
        .done(function(data) {
            percentage = JSON.parse(data)["percentage"].toFixed(2);
            $("#progressBar").css("width", percentage*100 + "%");
            $("#percentDone").html(percentage*100 + " %");
            getQuestion();
        });
    }

    getQuestion = function() {
        $.get("/tasks/get_next_question")
            .done(function(data) {
                var selections = [];
                var optText = [];
                var questionText;
                query = JSON.parse(data);

                if (query["question"][0] == null) {
                    ResetQFinal();
                }
                else {
                    question = JSON.parse(query["question"]);
                    questionText = question[0]["fields"]["text"];
                    opts = JSON.parse(query["options"]);
                    numOpts = opts.length;

                    numOpts = (numOpts > 5 ? 5 : numOpts);

                    for (i = 0; i < numOpts; i++) {
                        var opt = opts[i]["fields"];
                        number = opt["number"];
                        text = opt["text"];
                        optText.push(text);
                        selections.push(number);
                    }

                    questions.push(questionText);
                    options.push(optText);
                    optionNumbers.push(selections);
                    ResetQFinal();
                }
            });
    }

    getQuestionInitial = function() {
        $.get("/tasks/get_next_question")
            .done(function(data) {
                var selections = [];
                var optText = [];
                var questionText;
                query = JSON.parse(data);

                question = JSON.parse(query["question"]);
                if (question == "")
                    EndQuiz();
                questionText = question[0]["fields"]["text"];
                opts = JSON.parse(query["options"]);
                numOpts = opts.length;

                for (i = 0; i < numOpts; i++) {
                    var opt = opts[i]["fields"];
                    number = opt["number"];
                    text = opt["text"];
                    optText.push(text);
                    selections.push(number);
                }

                questions.push(questionText);
                options.push(optText);
                optionNumbers.push(selections);
                SetQuestions();
            });
    }

};



$(document).ready(function () {

    // resize the canvas
    $("#taskCanvas").attr("width", 550);
    $("#taskCanvas").attr("height", 600);

    // Start the quiz
    startExercise();

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

