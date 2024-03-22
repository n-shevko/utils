document.addEventListener('DOMContentLoaded', function() {
  new Vue({
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
          current_tab: null,
          progress: 0,
          progressMsg: null,
          inProgress: false,
          taskId: null
        },
        JSON.parse(document.getElementById('vue_data').textContent)
      );
    },
    watch: {
      'state': {
        handler(newValue, oldValue) {
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
        let handler = self[`${self.dialog}_post`];
        if (handler !== undefined) {
          handler();
        }
      })
    },
    methods: {
      update(args) {
         Object.keys(args.value).forEach(key => {
           this.$set(this, key, args.value[key]);
         });
      },
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
          self.state.selected_video = data.selected[0];
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
        this.inProgress = answer;
      },
      unlockRun(_) {
        this.inProgress = false;
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
      update_gpt_answer(args) {
        this.gpt_answer = args.answer;
        this.out_file = args.out_file;
        this.progress = args.progress;
        this.taskId = args.task_id;
      },
      copyResult() {
        navigator.clipboard.writeText(this.gpt_answer || this.state.script_cleaner_last_answer_gpt);
      },
      hideModal() {
        this.modal.hide();
      },
      selectVideo() {
        $('#jstree').jstree(true).destroy();
        this.modal.hide();
      },
      script_cleaner_run() {
        this.sendMessage({fn: 'script_cleaner_run'})
      },
      onMessage(event) {
        let request = JSON.parse(event.data);
        this[request.fn](request);
      },
      stopScriptCleaner() {
        this.sendMessage({fn: 'update', key: `stop_${this.taskId}`, value: '1'});
        this.inProgress = false;
      }
    }
  });
})