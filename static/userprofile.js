var last_i = '0';
var last_status = '';

var toggled = 0;

function select(i, username, dbid, status) {
  $('#' + last_i).removeClass('active_' + last_status);
  $('#' + i).addClass('active_' + status);
  last_i = i;
  last_status = status;
  $('#dcontent').slideUp(300, function() {
    $('#dcontent').html('<img src="/static/loading.gif" />');
    $('#dcontent').slideDown(300, function() {
      $.get('/ajax/entry', {index: i, user: username, db: dbid}, function(data){
        $('#dcontent').slideUp(300, function(){
          $('#dcontent').html(data);
          $('#dcontent').slideDown(300);
        })
      })
    });
  });
  
};

function toggle_info() {
  if (toggled == 0) {
    toggled = 1;
    $('#profile_info').hide(100, function(){
      $('#tbs').css('padding-left', '20px');
      $('#cont').css('padding-left', '20px');
      $('#dcontent').css('width', '90%');
      $('#butan').attr('src', '/static/forth.png');
    });
  } else {
    toggled = 0;
    $('#profile_info').show(100, function(){
      $('#tbs').css('padding-left', '250px');
      $('#cont').css('padding-left', '250px');
      $('#dcontent').css('width', '60%');
      $('#butan').attr('src', '/static/back.png');
  });
  };
};