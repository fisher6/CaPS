var selections = [];




function startQuiz() {

    var query;

    var canvas = document.getElementById("taskCanvas");
    var context = canvas.getContext("2d");
    var quizbg = new Image();
    var Question = new String;
    var Option1 = new String;
    var Option2 = new String;
    var Option3 = new String;
    var mx=0;
    var my=0;
    var CorrectAnswer = 0;
    var qnumber = 0;
    var rightanswers=0;
    var wronganswers=0;
    var QuizFinished = false;
    var lock = false;
    var textpos1=45;
    var textpos2=145;
    var textpos3=230;
    var textpos4=325;
    var Questions = [];
    var Options = [];
    var OptionNumbers = [];
    var chosen = [];

    quizbg.onload =
        function(){
            context.drawImage(quizbg, 0, 0);
            getQuestionInitial();
        }

    quizbg.src = "/static/tasks/images/quizbg.png";

    SetQuestions = function() {
        Question=Questions[qnumber];
        //CorrectAnswer=1+Math.floor(Math.random()*3);
        CorrectAnswer=0;
        Option1=Options[qnumber][0];
        Option2=Options[qnumber][1];
        Option3=Options[qnumber][2];

        /*
        if(CorrectAnswer==0) {
            Option1=Options[qnumber][0];
            Option2=Options[qnumber][1];
            Option3=Options[qnumber][2];
        }
        if(CorrectAnswer==1) {
            Option1=Options[qnumber][2];
            Option2=Options[qnumber][0];
            Option3=Options[qnumber][1];
        }
        if(CorrectAnswer==2) {
            Option1=Options[qnumber][1];
            Option2=Options[qnumber][2];
            Option3=Options[qnumber][0];
        }
        */

        context.textBaseline = "middle";
        context.font = "24pt Calibri,Arial";
        context.fillText(Question,20,textpos1);
        context.font = "18pt Calibri,Arial";
        context.fillText(Option1,20,textpos2);
        context.fillText(Option2,20,textpos3);
        context.fillText(Option3,20,textpos4);
      }

    canvas.addEventListener('click',ProcessClick,false);

    function ProcessClick(ev) {
        my=ev.y-canvas.offsetTop;
        if(ev.y == undefined){
            my = ev.pageY - canvas.offsetTop;
        }
        if(lock){
            ResetQ();
        }
        else{
            if(my>110 && my<180) {GetFeedback(0);}
            if(my>200 && my<270) {GetFeedback(1);}
            if(my>290 && my<360) {GetFeedback(2);}
        }
    }

    GetFeedback = function(a) {
        chosen[0] = OptionNumbers[qnumber][a];
        //console.log("CHOSEN: " + chosen[0]);
        context.drawImage(quizbg, 0,400,75,70,480,110+(90*(a)),75,70);

        /*
        if(a==CorrectAnswer){
            context.drawImage(quizbg, 0,400,75,70,480,110+(90*(a)),75,70);
            rightanswers++;
        }
        else{
            context.drawImage(quizbg, 75,400,75,70,480,110+(90*(a)),75,70);
            wronganswers++;
        }
        */
        lock=true;
        context.font = "14pt Calibri,Arial";
        context.fillText("Click again to continue",20,380);
    }

    ResetQ = function() {
        sendAnswer(chosen);
    }

    ResetQFinal = function() {
        lock=false;
        context.clearRect(0,0,550,400);
        qnumber++;
        if(qnumber==Questions.length){EndQuiz();}
        else{
            context.drawImage(quizbg, 0, 0);
            SetQuestions();}
    }

    EndQuiz = function() {
        canvas.removeEventListener('click',ProcessClick,false);
        context.drawImage(quizbg, 0,0,550,90,0,0,550,400);
        context.font = "20pt Calibri,Arial";
        context.fillText("You have finished the exercise!",20,100);
        //context.font = "16pt Calibri,Arial";
        //context.fillText("Correct answers: "+String(rightanswers),20,200);
        //context.fillText("Wrong answers: "+String(wronganswers),20,240);
    }

    sendAnswer = function(e) {
        //console.log("Sending: " + e);
        $.post({
            url: '/tasks/send_response/',
            contentType: 'application/json; charset=utf-8',
            processData: false,
            data: JSON.stringify(e)
        })
        .done(function(data) {
            //console.log("!!!!!!!!! " + data);
            percentage = JSON.parse(data)["percentage"].toFixed(2);
            //console.log(percentage);
            $("#progressBar").css("width", percentage*100 + "%");
            $("#percentDone").html(percentage*100 + " %");
            getQuestion();
        });
    }

    getQuestion = function() {
        //console.log("Getting question for " + qnumber);
        $.get("/tasks/get_next_question/")
            .done(function(data) {
                console.log(data);
                var selections = [];
                var optText = [];
                var questionText;
                query = JSON.parse(data);

                //console.log(question);
                //console.log(query["question"][0]);
                if (query["question"][0] == null) {
                    ResetQFinal();
                }
                else {
                    //console.log(query["options"]);
                    question = JSON.parse(query["question"]);
                    questionText = question[0]["fields"]["text"];
                    //console.log(questionText);
                    opts = JSON.parse(query["options"]);
                    numOpts = opts.length;
                    //console.log(numOpts);

                    for (i = 0; i < numOpts; i++) {
                        var opt = opts[i]["fields"];
                        //console.log(opt);
                        number = opt["number"];
                        text = opt["text"];
                        //console.log(text);
                        optText.push(text);
                        selections.push(number);
                    }

                    Questions.push(questionText);
                    Options.push(optText);
                    OptionNumbers.push(selections);
                    ResetQFinal();

                    //sendAnswer(selections);
                }
            });
    }

    getQuestionInitial = function() {
        //console.log("Getting question for " + qnumber);
        $.get("/tasks/get_next_question/")
            .done(function(data) {
                console.log(data);
                var selections = [];
                var optText = [];
                var questionText;
                query = JSON.parse(data);

                //console.log(question);
                //console.log("QUESTION " + query["question"]);
                //console.log(query["options"]);
                question = JSON.parse(query["question"]);
                if (question == "")
                    EndQuiz();
                questionText = question[0]["fields"]["text"];
                //console.log(questionText);
                opts = JSON.parse(query["options"]);
                numOpts = opts.length;
                //console.log(numOpts);

                for (i = 0; i < numOpts; i++) {
                    var opt = opts[i]["fields"];
                    //console.log(opt);
                    number = opt["number"];
                    text = opt["text"];
                    //console.log(text);
                    optText.push(text);
                    selections.push(number);
                }

                Questions.push(questionText);
                Options.push(optText);
                OptionNumbers.push(selections);
                SetQuestions();

                //sendAnswer(selections);
            });
    }

};



$(document).ready(function () {
  // Start the quiz
  startQuiz();

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

