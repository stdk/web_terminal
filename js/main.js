(function() {
  Terminal.applyAddon(fit)
  Terminal.applyAddon(attach)

  var term = new Terminal({
    cursorStyle: "block",
    "fontSize": localStorage.fontSize || 16,
    "fontFamily": localStorage.fontFamily || "Monospace",
    "theme": document.themes[localStorage.theme] || {}
  })

  //term.setOption('theme', theme);

  window.onresize = function(event) {
    term.fit()
  };

  window.addEventListener('beforeunload', function (e) {
    e.preventDefault();
    e.returnValue = 'Leave?';
  });

  var term_element = document.getElementById('terminal')
  console.log(term_element.offsetHeight);
  term.open(term_element)
  term.fit()

  var ws_base_path = 'ws://' + location.host + '/ws'
  var list_element = document.getElementById('list')

  if(location.pathname == '/') {
    term_element.style.height = '94%'
    term.fit()

    var ws = new WebSocket(ws_base_path + '/list')
    ws.addEventListener('open', function(event) {
      ws.send(JSON.stringify({
        action:'get'
      }))
    })

    ws.addEventListener('message',function(event) {
      var response = JSON.parse(event.data)
      console.log(response)

      list_element.innerHTML = ''

      available = response.available

      available.sort(function(a, b){
        return a.title.localeCompare(b.title, undefined, {numeric: true, sensitivity: 'base'})
      });

      for(var i=0;i<available.length;++i) {
        let entry = available[i]
        let title = entry.title
        let comment = entry.comment
        list_element.innerHTML += '<div><div id="comment_' + title + '" contenteditable="true">' +
                                  comment +
                                  '</div>' +
                                  '<button class="console_button" type="button">' + 
                                  title + 
                                  '</button>' +
                                  '</div>'
      }
      //list_element.style.display = 'none'
      /*list_element.style.display = 'flex'
      list_element.style.display = 'none'*/
      list_element.style.display = 'flex'

      for(var i=0;i<available.length;++i) {
        let entry = available[i]
        let title = entry.title
        let comment_element = document.getElementById("comment_" + title)
        comment_element.addEventListener("input", function() {
          let comment = comment_element.innerText
          ws.send(JSON.stringify({
            action: 'set',
            title: title,
            comment: comment
          }))
        }, false);
      }

      var selectedButton = undefined

      var buttons = document.getElementsByClassName('console_button')
      for(var i=0;i<buttons.length;++i) {
        let button = buttons[i]
        let entry = available[i]
        console.log(entry)
        button.addEventListener('click',function(button,entry) {
            return function() {
              window.document.title = entry.title
              if (selectedButton)  {
                selectedButton.classList.remove('selected')
              }

              button.classList.add('selected')
              selectedButton = button

              term.detach()
              term.clear()
              term.reset()
              
              var console_ws = new WebSocket(ws_base_path + entry.path)
              term.attach(console_ws)

              term.focus()
            }
        }(button,entry))
      }        
    })
  } else {
    term.clear()
    term.reset()

    console.log(ws_base_path + '/remote?title=' + location.pathname.substr(1))
    var console_ws = new WebSocket(ws_base_path + '/remote?title=' + location.pathname.substr(1))
    term.attach(console_ws)

    term.focus({"focus": true})
  }
})()