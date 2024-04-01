script_cleaner = {
  data: {
    progress: 0,
    progressMsg: null,
    inProgress: false,
    taskId: null
  },
  methods: {
    runChatgpt(answer) {
      if (answer) {
        this.sendMessage({fn: 'run_chatgpt', answer: true, delimeter: this.delimeter});
      } else {
        this.unlockRun();
      }
      this.modal.hide();
    },
    unlockRun() {
      this.inProgress = false;
      this.modal.hide();
    },
    copyResult() {
      navigator.clipboard.writeText(this.state.script_cleaner_last_answer_gpt);
    },
    script_cleaner_run() {
      this.inProgress = true;
      this.sendMessage({fn: 'script_cleaner_run'})
    },
    stopScriptCleaner() {
      this.sendMessage({fn: 'update', key: `stop_${this.taskId}`, value: '1'});
      this.inProgress = false;
    },
  }
};