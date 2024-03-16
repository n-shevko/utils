document.addEventListener('DOMContentLoaded', function() {
  var app = new Vue({
    el: '#app',
    data() {
      return Object.assign({
          ws: null,
          message: 'Hello'
        },
        JSON.parse(document.getElementById('vue_data').textContent)
      );
    },
    created: function () {
      this.ws = new WebSocket(`ws://${window.location.host}/ws/worker`);
      this.ws.onmessage = this.onMessage;
    },
    methods: {
      switchTab(name) {
        this.sendMessage({fn: 'switch_tab', name: name});
        this.config.current_tab = name;
      },
      sendMessage(msg) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
          this.ws.send(JSON.stringify(msg));
        } else {
          console.error('WebSocket is not open. Unable to send message.');
        }
      }
    }
  });
})