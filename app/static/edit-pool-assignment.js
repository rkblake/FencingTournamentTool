function shuffle(array) {
  var currentIndex = array.length, temporaryValue, randomIndex;

  // While there remain elements to shuffle...
  while (0 !== currentIndex) {

    // Pick a remaining element...
    randomIndex = Math.floor(Math.random() * currentIndex);
    currentIndex -= 1;

    // And swap it with the current element.
    temporaryValue = array[currentIndex];
    array[currentIndex] = array[randomIndex];
    array[randomIndex] = temporaryValue;
  }

  return array;
}
    
$( function() {
  $( ".connectedSortable" ).sortable({
    connectWith: ".connectedSortable"
  }).disableSelection();
} );
    
function randomizeInPools() {
  $('ul').each(function(){
    var $ul = $(this);
    var $liArr = $ul.children('li');
    $liArr = shuffle($liArr);
    $ul.append($liArr);
  });
}
    
function randomizeAllPools() {
  var $allLi = [];
  var liSize = [];
  var i = 0;
  $('ul').each(function() {
    var $this = $(this);
    var $children = $this.children('li');
    $allLi = $allLi.concat($children.toArray());
    liSize[i++] = $children.length;
  });
  $allLi = shuffle($allLi);

  i = 0;
  $('ul').each(function(i2, v) {
    $(this).append($allLi.slice(i, i+liSize[i2]));
    i += liSize[i2];
  });
}

$(function() {
    var form = document.getElementById('form1');

    form.onsubmit = function (e) {
    // stop the regular form submission
    e.preventDefault();

    // collect the form data while iterating over the inputs
    var data = {};
    $('ul').each(function(i, v) {
        var $this = $(this);
        data[i] = $this.find('.ui-state-default').map(function() {return $(this).text()}).toArray();
    });

    // construct an HTTP request
    var xhr = new XMLHttpRequest();
    xhr.open(form.method, form.action, true);
    xhr.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');

    // send the collected data as JSON
    console.log(JSON.stringify(data));
    xhr.send(JSON.stringify(data));

    xhr.onloadend = function () {
      // done
    };
  };
});
