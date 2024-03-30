document.addEventListener('DOMContentLoaded', function() {
  let vue_data = JSON.parse(document.getElementById('vue_data').textContent);
  let mixins = [];
  vue_data.menu.forEach(item => {
    if (window[item.name] !== undefined) {
      mixins.push(window[item.name]);
    }
  })

  new Vue({
    el: '#app',
    mixins: mixins,
    data() {
      return Object.assign({
          ws: null,
          dialogTitle: null,
          fileDst: null,
          ignoreNextUpdate: false,
          dialog: null,
          modal: null,
          msg: null,
          current_tab: null,
        },
        vue_data
      );
    },
    watch: {
      'state': {
        handler(newValue, oldValue) {
          if (this.ignoreNextUpdate) {
            this.ignoreNextUpdate = false;
            return
          }
          Object.keys(newValue).forEach(key => {
            this.sendMessage({fn: 'update',  key: key, value: newValue[key]});
          });
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
      document.getElementById('modal').addEventListener('shown.bs.modal', event => {
        if (self.dialog === 'select_file') {
          this.initJsTree();
        }
      })
    },
    methods: {
      update(args) {
        Object.keys(args.value).forEach(key => {
          if (key.indexOf('.') !== -1) {
            let keys = key.split('.');
            if (keys[0] === 'state') {
              this.ignoreNextUpdate = true;
            }
            this.$set(this[keys[0]], keys[1], args.value[key])
          } else {
            this[key] = args.value[key];
          }
        });
        if (args.callback !== undefined) {
          this[args.callback]();
        }
      },
      initModal() {
        this.modal = new bootstrap.Modal(document.getElementById('modal'));
        this.modal.show();
      },
      openModal(val, dialogTitle, fileDst){
        this.dialog = val;
        this.dialogTitle = dialogTitle;
        this.fileDst = fileDst;
        this.initModal();
      },
      initJsTree() {
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
        let self = this;
        $('#jstree').on("changed.jstree", function (e, data) {
          if (data.selected[0] === undefined) {
            return
          }
          self.state[self.fileDst] = data.selected[0];
        });
      },
      dialogAnswer(answer) {
        this[this.dialogCallback](answer)
      },
      switchTab(name) {
        this.sendMessage({fn: 'update', key: 'current_tab', value: name});
        this.current_tab = name;
        this.sendMessage({fn: 'get_state', current_tab: name});
      },
      sendMessage(msg) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
          this.ws.send(JSON.stringify(msg));
        } else {
          console.error('WebSocket is not open. Unable to send message.');
        }
      },
      hideModal() {
        this.modal.hide();
      },
      closeFileSelect() {
        $('#jstree').jstree(true).destroy();
        this.modal.hide();
      },
      onMessage(event) {
        let request = JSON.parse(event.data);
        this[request.fn](request);
      }
    }
  });
})