(function() {
  var term = new Terminal({
    cursorBlink: false,  // Do not blink the terminal's cursor
  })

  window.onresize = function(event) {
    term.fit()
  };

  window.addEventListener('beforeunload', function (e) {
    e.preventDefault();
    e.returnValue = 'Leave?';
  });

  var term_element = document.getElementById('terminal')
  term.open(term_element)
  term.fit()

  var ws_base_path = 'ws://' + location.host + '/ws'
  var list_element = document.getElementById('list')

  if(location.pathname == '/') {
    list_element.style.height = '8vh'
    term_element.style.height = '90vh'
    term.fit()

    var ws = new WebSocket(ws_base_path + '/list')
    ws.addEventListener('message',function(event) {
      var response = JSON.parse(event.data)
      console.log(response)
      available = response.available
      for(var i=0;i<available.length;++i) {
        list_element.innerHTML += '<button class="console_button" type="button">' +
         available[i].title + '</button>'
      }
      var buttons = document.getElementsByClassName('console_button')
      for(var i=0;i<buttons.length;++i) {
        var button = buttons[i]
        var path = available[i].path
        button.addEventListener('click',function(path) {
            return function() {
              term.detach()
              term.clear()
              term.reset()
              
              var console_ws = new WebSocket(ws_base_path + path)
              term.attach(console_ws)

              term.focus()
            }
        }(path))
      }        
    })
  } else {
    term.clear()
    term.reset()

    console.log(ws_base_path + '/remote?title=' + location.pathname.substr(1))
    var console_ws = new WebSocket(ws_base_path + '/remote?title=' + location.pathname.substr(1))
    term.attach(console_ws)

    term.focus()
  }
})()