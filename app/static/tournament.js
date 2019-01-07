$(document).ready(function(){
    $(".event-header").click(function(){
      $(this).next(".event-sub").slideToggle(125);
    });
});
