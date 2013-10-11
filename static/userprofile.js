var last_i = '0';
var last_status = '';

var toggled = 0;

$(document).ready(function() {
  $.each($('[id^=sort_btn]'), function(index, value) {
    $(value).click(function(){
      $('[id^=sort_btn]').removeClass('sort_btn_active');
      $(value).addClass('sort_btn_active');
      $('#listNav').slideUp(2000, function() {
        $('#listNav').html('<img src="/static/loading.gif" style="padding-left: 20px;" />');
        $('#listNav').slideDown(250, function(){
          $.get('/orderedDb/' + user + '/' + db + '/' + $(value).attr('id'), function(data) {
            $('#listNav').slideUp(250, function() {
              $('#listNav').html(data);
              $('#listNav').slideDown(2000);
            });
          });
        });
      });
    });
  });
});


function select(i, username, dbid, status) {
  $('#' + last_i).removeClass('active_' + last_status);
  $('#' + i).addClass('active_' + status);
  last_i = i;
  last_status = status;

  $('#dc').stop().animate({marginTop: $(window).scrollTop()});

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
      $('#butan').text('show panel');
      $('#butan').css('position', 'absolute');
    });
  } else {
    toggled = 0;
    $('#profile_info').show(100, function(){
      $('#tbs').css('padding-left', '250px');
      $('#cont').css('padding-left', '250px');
      $('#dcontent').css('width', '60%');
      $('#butan').text('hide panel');
      $('#butan').css('position', 'fixed');
  });
  };
};

function showBiography(name, id) {
  $('#biography').slideUp(300, function() {
    $('#biography').html('<br /><img src="/static/loading.gif" />');
    $('#biography').slideDown(300, function() {
      $.get('/ajax/biography', {name: name, id: id}, function(data){
        $('#biography').slideUp(300, function(){
          $('#biography').html(data);
          $('#biography').slideDown(300);
        })
      })
    });
  });
};
