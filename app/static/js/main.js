document.addEventListener('DOMContentLoaded', function() {
  var app = new Vue({
    el: '#app',
    data() {
      return Object.assign({
          ws: null,
          dialogTitle: null,
          dialog: null,
          modal: null,
          msg: null,
          gpt_answer: null,
          out_file: null,
          progress: null,
          disableRun: false
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
      document.getElementById('modal').addEventListener('shown.bs.modal', event => {
        let handler = self[`${self.dialog}_post`];
        if (handler !== undefined) {
          handler();
        }
      })
    },
    methods: {
      initModal() {
        this.modal = new bootstrap.Modal(document.getElementById('modal'));
        this.modal.show();
      },
      openModal(val){
        this.dialog = val;
        this.initModal();
      },
      select_video_post() {
        this.dialogTitle = 'Select video';
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
          self.config.selected_video = data.selected[0];
        });
      },
      yes_no_dialog(args) {
        this.dialogTitle = args.title;
        this.msg = args.msg;
        this.dialog = 'yes_no_dialog';
        this.dialogResponse = args.response;
        this.initModal();
      },
      notify_dialog(args) {
        this.dialogTitle = args.title;
        this.msg = args.msg;
        this.dialog = 'notify_dialog';
        if (args.callback !== undefined) {
          this[args.callback](args);
        }
        this.initModal();
      },
      dialogAnswer(answer) {
        this.dialogResponse['answer'] = answer
        this.sendMessage(this.dialogResponse);
        this.modal.hide();
        this.disableRun = answer;
      },
      unlockRun(_) {
        this.disableRun = false;
      },
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
      update_gpt_answer(args) {
        this.gpt_answer = args.answer;
        this.out_file = args.out_file;
        this.progress = args.progress;
      },
      copyResult() {
        navigator.clipboard.writeText(this.gpt_answer || this.config.script_cleaner_last_answer_gpt);
      },
      hideModal() {
        this.modal.hide();
      },
      selectVideo() {
        $('#jstree').jstree(true).destroy();
        this.modal.hide();
      },
      script_cleaner_run() {
        this.config.script_cleaner_stop = false;
        this.sendMessage({fn: 'script_cleaner_run'})
      },
      onMessage(event) {
        let request = JSON.parse(event.data);
        this[request.fn](request);
      },
      stopScriptCleaner() {
        this.sendMessage({fn: 'update_config', config: {script_cleaner_stop: true}}); // why watch not work
      }
    }
  });
})