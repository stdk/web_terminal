  (function() {
    var convertTheme = function(theme) {
    let color = theme.color
    return {
      "foreground": theme.foreground,
      "background": theme.background,
      "cursor": theme.foreground,
      "black": color[0],
      "red": color[1],
      "green": color[2],
      "yellow": color[3],
      "blue": color[4],
      "magenta": color[5],
      "cyan": color[6],
      "white": color[7],
      "brightBlack": color[8],
      "brightRed": color[9],
      "brightGreen": color[10],
      "brightYellow": color[11],
      "brightBlue": color[12],
      "brightMagenta": color[13],
      "brightCyan": color[14],
      "brightWhite": color[15],
    }
  }

  var greenTheme = convertTheme({
   "color": [
     "#001100",
     "#007700",
     "#00bb00",
     "#007700",
     "#009900",
     "#00bb00",
     "#005500",
     "#00bb00",
     "#007700",
     "#007700",
     "#00bb00",
     "#007700",
     "#009900",
     "#00bb00",
     "#005500",
     "#00ff00"
   ],
   "foreground": "#00bb00",
   "background": "#000000"
  })

  var monokaiTheme = convertTheme({
   "color": [
     "#272822",
     "#f92672",
     "#a6e22e",
     "#f4bf75",
     "#66d9ef",
     "#ae81ff",
     "#a1efe4",
     "#f8f8f2",
     "#75715e",
     "#f92672",
     "#a6e22e",
     "#f4bf75",
     "#66d9ef",
     "#ae81ff",
     "#a1efe4",
     "#f9f8f5"
   ],
   "foreground": "#f8f8f2",
   "background": "#272822"
  })

  var forestTheme = convertTheme({
    "color": [
     "#1b1918",
     "#f22c40",
     "#5ab738",
     "#d5911a",
     "#407ee7",
     "#6666ea",
     "#00ad9c",
     "#a8a19f",
     "#766e6b",
     "#f22c40",
     "#5ab738",
     "#d5911a",
     "#407ee7",
     "#6666ea",
     "#00ad9c",
     "#f1efee"
   ],
   "foreground": "#a8a19f",
   "background": "#1b1918"
  })

  var phrak1Theme = convertTheme({
    "color": [
     "#000000",
     "#a80000",
     "#00a800",
     "#a85400",
     "#0000a8",
     "#a800a8",
     "#00a8a8",
     "#a8a8a8",
     "#545054",
     "#f85450",
     "#50fc50",
     "#f8fc50",
     "#5054f8",
     "#f854f8",
     "#50fcf8",
     "#f8fcf8"
   ],
   "foreground": "#a8a8a8",
   "background": "#000000"
  })

  document.themes = {
    "green": greenTheme,
    "monokai": monokaiTheme,
    'forest':forestTheme,
    'phrak1':phrak1Theme,
  }
})()