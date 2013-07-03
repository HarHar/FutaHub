var last_i = '0';
var last_status = '';

function select(i, status) {
  $('#' + last_i).removeClass('active_' + last_status);
  $('#' + i).addClass('active_' + status);
  last_i = i;
  last_status = status;
  $('#dcontent').slideUp(300, function() {
    $('#dcontent').html('<img src="/static/loading.gif" />');
    $('#dcontent').slideDown(300, function() {
      $.get('/ajax/entry/' + i, function(data){
        $('#dcontent').slideUp(300, function(){
          $('#dcontent').html(data);
          $('#dcontent').slideDown(300);
        })
      })
    });
  });
  
};