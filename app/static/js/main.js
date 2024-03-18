document.addEventListener('DOMContentLoaded', function() {
  var app = new Vue({
    el: '#app',
    data() {
      return Object.assign({
          ws: null
        },
        JSON.parse(document.getElementById('vue_data').textContent)
      );
    },
    watch: {
      'config': {
        handler(newValue, oldValue) {
          this.sendMessage({fn: 'update_config', config: newValue});
        },
        deep: true
      }
    },
    created: function () {
      this.ws = new WebSocket(`ws://${window.location.host}/ws/worker`);
      this.ws.onmessage = this.onMessage;
    },
    mounted: function () {
      let self = this;
      document.getElementById('selectVideo').addEventListener('show.bs.modal', event => {
        $('#jstree').jstree({
          'core' : {
            'multiple' : false,
            'data' : {
              'url' : 'files',
              'data' : function (node) {
                return { 'id' : node.id };
              }
            }
          },
          'plugins' : ['checkbox']
        });
        $('#jstree').on("changed.jstree", function (e, data) {
          self.config.selected_video = data.selected[0];
        });
      })
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
      },
      selectVideo() {
        $('#jstree').jstree(true).destroy();
        $('#selectVideo').modal('hide');
      }
    }
  });
})